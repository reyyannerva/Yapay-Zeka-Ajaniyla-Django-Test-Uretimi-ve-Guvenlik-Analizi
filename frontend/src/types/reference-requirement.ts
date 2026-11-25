// docs/api/reference-requirements.md — iskelet; #40/#41 genişletir.
export type RequirementCategory = 'ROLE' | 'ACCESS_RULE' | 'DEPLOY_EXPECTATION';
export type RequirementSource = 'FORM' | 'JSON_UPLOAD';
export type HttpMethod = 'GET' | 'POST' | 'PUT' | 'PATCH' | 'DELETE';

export interface RoleSpecification {
  schema_version: 1;
  role: string;
}

export interface AccessRuleSpecification {
  schema_version: 1;
  endpoint: string;
  method: HttpMethod;
  expected_status_by_role: Record<string, number>;
}

export interface DeployExpectationSpecification {
  schema_version: 1;
  setting: string;
  expected_value: unknown;
  check_id?: string;
}

export type ReferenceSpecification =
  | RoleSpecification
  | AccessRuleSpecification
  | DeployExpectationSpecification;

export interface ReferenceRequirement {
  id: number;
  /** Proje kimliği */
  project: number;
  requirement_code: string;
  category: RequirementCategory;
  source?: RequirementSource;
  title: string;
  description?: string;
  expected_result?: string;
  specification?: ReferenceSpecification;
  is_active?: boolean;
  revision: number;
  http_method: HttpMethod | null;
  created_at: string;
  updated_at: string;
}
