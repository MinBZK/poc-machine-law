// See https://kit.svelte.dev/docs/types#app
// for information about these interfaces
declare global {
  namespace App {
    // interface Error {}
    // interface Locals {}
    // interface PageData {}
    // interface PageState {}
    // interface Platform {}
  }
}

export interface Law {
	$id: string;
	uuid: string;
	name: string;
	law: string;
	law_type?: string;
	legal_character?: string;
	decision_type?: string;
	valid_from: string;
	service: string;
	legal_basis: LegalBasis;
	description: string;
	references: Reference[];
	properties: Properties;
	actions: Action[];
	definitions?: Record<string, (string[] | number)>;

	source: string; // Original YAML source
}

export interface LegalBasis {
	law: string;
	bwb_id: string;
	article: string;
	paragraph?: string;
	url: string;
	juriconnect: string;
	explanation: string;
}

export interface Reference {
	law: string;
	article: string;
	url: string;
	description?: string;
}

export interface Properties {
	parameters?: Parameter[];
	sources?: Source[];
	input?: Input[];
	output?: Output[];
}

export interface BaseProperty {
    name: string;
    description: string;
    type: string;
    legal_basis: LegalBasis;
}

export interface Parameter extends BaseProperty {
	required: boolean;
}

export interface Source extends BaseProperty {
	temporal: Temporal;
	source_reference: SourceReference;
}

export interface Input extends BaseProperty {
	type_spec?: TypeSpec;
	service_reference: ServiceReference;
	temporal: Temporal;
}

export interface Output extends BaseProperty {
	type_spec?: TypeSpec;
	temporal: Temporal;
}

export interface Temporal {
	type: 'period' | 'point_in_time' | 'continuous';
	period_type?: 'month' | 'year' | 'continuous';
	reference?: string;
}

export interface SourceReference {
	table: string;
	field?: string;
	fields?: string[];
	select_on: SelectOn[];
}

export interface SelectOn {
	name: string;
	description: string;
	type: string;
	value: string;
}

export interface ServiceReference {
	service: string;
	field: string;
	law: string;
	parameters?: ServiceParameter[];
}

export interface ServiceParameter {
	name: string;
	reference: string;
}

export interface TypeSpec {
	unit: string;
	precision: number;
	min: number;
}

export type ActionValue = string | number | boolean | Action;

export interface Action {
	output?: string;
	operation: string;
	values?: ActionValue[];
	subject?: string | Action;
	value?: any;
	legal_basis?: LegalBasis;
	conditions?: (Condition | ElseCondition)[];
    combine?: 'OR' | 'AND';
}

export interface Condition {
	test: Action;
	then: any;
}

export interface ElseCondition {
    else: any;
}

export {};
