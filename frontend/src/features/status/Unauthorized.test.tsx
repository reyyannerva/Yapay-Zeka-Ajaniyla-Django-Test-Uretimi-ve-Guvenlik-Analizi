import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { expect, test } from "vitest";

import { ToastProvider } from "../../components/ui/Toast";
import { MOCK_FORBIDDEN_PROJECT_ID } from "../../lib/api/mock";
import { ROUTER_FUTURE } from "../../test/router-future";
import { ProjectDetail } from "../projects/ProjectDetail";
import { NotFound } from "./NotFound";
import { Unauthorized } from "./Unauthorized";

function renderAt(path: string) {
  const client = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  return render(
    <QueryClientProvider client={client}>
      <ToastProvider>
        <MemoryRouter initialEntries={[path]} future={ROUTER_FUTURE}>
          <Routes>
            <Route path="/dashboard" element={<p>Panel sayfası</p>} />
            <Route path="/forbidden" element={<Unauthorized />} />
            <Route path="/projects/:id" element={<ProjectDetail />} />
            <Route path="*" element={<NotFound />} />
          </Routes>
        </MemoryRouter>
      </ToastProvider>
    </QueryClientProvider>,
  );
}

test("başkasının projesi (403) açılınca yetkisiz erişim ekranı (13) görünür", async () => {
  renderAt(`/projects/${MOCK_FORBIDDEN_PROJECT_ID}`);
  expect(
    await screen.findByRole("heading", {
      name: "Bu sayfaya erişim yetkiniz yok",
    }),
  ).toBeInTheDocument();
  expect(screen.queryByText("Proje bulunamadı")).not.toBeInTheDocument();
});

test("olmayan proje (404) yetkisiz ekranına düşmez", async () => {
  renderAt("/projects/999");
  expect(await screen.findByText("Proje bulunamadı")).toBeInTheDocument();
  expect(
    screen.queryByText("Bu sayfaya erişim yetkiniz yok"),
  ).not.toBeInTheDocument();
});

test('"Panele dön" bağlantısı /dashboard\'a gider', async () => {
  renderAt("/forbidden");
  const link = screen.getByRole("link", { name: "Panele dön" });
  expect(link).toHaveAttribute("href", "/dashboard");
  await userEvent.click(link);
  expect(screen.getByText("Panel sayfası")).toBeInTheDocument();
});

test("bilinmeyen rota NotFound gösterir ve panele döndürür", async () => {
  renderAt("/boyle-bir-sayfa-yok");
  expect(
    screen.getByRole("heading", { name: "Sayfa bulunamadı" }),
  ).toBeInTheDocument();
  await userEvent.click(screen.getByRole("link", { name: "Panele dön" }));
  expect(screen.getByText("Panel sayfası")).toBeInTheDocument();
});
