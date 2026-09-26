"""GENERATED — do not edit by hand; regenerate from the API specs.

Typed keyword-parameter definitions for each endpoint, used as
``**params: Unpack[XxxParams]`` so IDEs autocomplete every filter name.
"""
from __future__ import annotations

from typing_extensions import TypedDict


class ActivityDetailsParams(TypedDict, total=False):
    entityId: str

class ActivityFeedParams(TypedDict, total=False):
    entityId: str
    cursor: str
    start: int

class ActivityReactionsParams(TypedDict, total=False):
    entityId: str
    start: int

class ActivityRepliesByAuthorParams(TypedDict, total=False):
    entityId: str
    cursor: str
    start: int

class ActivityRepliesParams(TypedDict, total=False):
    entityId: str
    sortBy: str
    count: int
    start: int

class CompaniesBatchEnrichParams(TypedDict, total=False):
    job_id: str
    after: int

class CompaniesCompanyParams(TypedDict, total=False):
    id: str
    slug: str

class CompaniesEmployeesParams(TypedDict, total=False):
    current_only: bool
    title: str
    geo_country_code: str
    geo_city: str
    start_year: int
    start_month: int
    sort: str
    cursor: str
    limit: int

class CompaniesSearchParams(TypedDict, total=False):
    name: str
    website: str
    staff_count_min: int
    staff_count_max: int
    follower_count_min: int
    follower_count_max: int
    industries: str
    industries_v2: str
    hq_city: str
    hq_country_code: str
    founded: int
    cursor: str
    limit: int

class DiscoverOpportunitiesParams(TypedDict, total=False):
    keyword: str
    sortBy: str
    datePosted: str
    experience: str
    jobTypes: str
    workplaceTypes: str
    salary: str
    companies: str
    industries: str
    locations: str
    functions: str
    titles: str
    benefits: str
    commitments: str
    easyApply: str
    verifiedJob: str
    under10Applicants: str
    fairChance: str
    count: int
    start: int

class DiscoverOrganizationsParams(TypedDict, total=False):
    keyword: str
    headcountRange: str
    industry: str
    geoEntityId: str
    hasJobs: str
    count: int
    start: int

class DiscoverPeopleParams(TypedDict, total=False):
    keyword: str
    firstName: str
    lastName: str
    title: str
    currentCompany: str
    pastCompany: str
    school: str
    industry: str
    geoEntityId: str
    profileLanguage: str
    serviceCategory: str
    count: int
    start: int

class FindBatchParams(TypedDict, total=False):
    job_id: str
    after: int

class FindLinkedinParams(TypedDict, total=False):
    url: str

class FindParams(TypedDict, total=False):
    first_name: str
    last_name: str
    domain: str

class InstitutionsAlumniParams(TypedDict, total=False):
    current_only: bool
    degree: str
    field_of_study: str
    start_year_min: int
    start_year_max: int
    end_year_min: int
    end_year_max: int
    geo_country_code: str
    geo_city: str
    sort: str
    page: int
    limit: int

class InstitutionsInstitutionParams(TypedDict, total=False):
    normalized_name: str

class InstitutionsSearchParams(TypedDict, total=False):
    name: str
    page: int
    limit: int

class JobChangesSearchParams(TypedDict, total=False):
    event_type: str
    organization_ids: str
    geo_city: str
    geo_country_code: str
    title: str
    days_ago: int
    page: int
    limit: int

class OpportunityByPersonParams(TypedDict, total=False):
    personEntityId: str
    count: int
    start: int

class OpportunityDetailsParams(TypedDict, total=False):
    opportunityEntityId: str

class OpportunityHiringTeamParams(TypedDict, total=False):
    opportunityEntityId: str

class OpportunityRelatedViewsParams(TypedDict, total=False):
    opportunityEntityId: str

class OpportunitySimilarParams(TypedDict, total=False):
    opportunityEntityId: str

class OrganizationActivitiesParams(TypedDict, total=False):
    id: str
    start: int

class OrganizationAffiliatedParams(TypedDict, total=False):
    id: str

class OrganizationEnrichParams(TypedDict, total=False):
    id: str

class OrganizationHeadcountParams(TypedDict, total=False):
    id: str

class OrganizationOpportunitiesParams(TypedDict, total=False):
    organizationEntityIds: str
    start: int

class OrganizationResolveSlugParams(TypedDict, total=False):
    slug: str

class OrganizationSimilarParams(TypedDict, total=False):
    id: str

class PeopleBatchEnrichParams(TypedDict, total=False):
    job_id: str
    after: int

class PeopleProfileParams(TypedDict, total=False):
    id: str
    handle: str

class PeopleSearchParams(TypedDict, total=False):
    first_name: str
    last_name: str
    headline: str
    summary: str
    geo_city: str
    geo_country_code: str
    is_creator: bool
    is_premium: bool
    primary_language: str
    skills: str
    skills_match: str
    organization_slugs: str
    current_only: bool
    title: str
    institution_ids: str
    certifications: str
    certification_authority: str
    last_change_within_days: int
    last_change_type: str
    tenure_min_years: int
    tenure_max_years: int
    company_count_min: int
    company_count_max: int
    current_company_count_min: int
    is_boomerang: bool
    education_level: str
    degree: str
    field_of_study: str
    skill_count_min: int
    skill_count_max: int
    speaks_language: str
    follower_count_min: int
    company_size_min: int
    company_size_max: int
    industry: str
    experience_min_years: int
    function: str
    function_min_years: int
    description: str
    exclude_titles: str
    exclude_organization_slugs: str
    exclude_industries: str
    cursor: str
    limit: int

class PersonEmploymentHistoryParams(TypedDict, total=False):
    entityId: str

class PersonEndorsementsParams(TypedDict, total=False):
    entityId: str

class PersonEnrichParams(TypedDict, total=False):
    entityId: str
    handle: str

class PersonInterestsParams(TypedDict, total=False):
    entityId: str

class PersonLookalikesParams(TypedDict, total=False):
    entityId: str

class PersonResolveHandleParams(TypedDict, total=False):
    handle: str

class ProspectsParams(TypedDict, total=False):
    domain: str
    kind: str
    cursor: str

class ReverseParams(TypedDict, total=False):
    email: str

class SkillsSearchParams(TypedDict, total=False):
    name: str
    page: int
    limit: int

class SkillsSkillParams(TypedDict, total=False):
    id: str

class VerifyBatchParams(TypedDict, total=False):
    job_id: str
    after: int

class VerifyParams(TypedDict, total=False):
    email: str

__all__ = ["ActivityDetailsParams", "ActivityFeedParams", "ActivityReactionsParams", "ActivityRepliesByAuthorParams", "ActivityRepliesParams", "CompaniesBatchEnrichParams", "CompaniesCompanyParams", "CompaniesEmployeesParams", "CompaniesSearchParams", "DiscoverOpportunitiesParams", "DiscoverOrganizationsParams", "DiscoverPeopleParams", "FindBatchParams", "FindLinkedinParams", "FindParams", "InstitutionsAlumniParams", "InstitutionsInstitutionParams", "InstitutionsSearchParams", "JobChangesSearchParams", "OpportunityByPersonParams", "OpportunityDetailsParams", "OpportunityHiringTeamParams", "OpportunityRelatedViewsParams", "OpportunitySimilarParams", "OrganizationActivitiesParams", "OrganizationAffiliatedParams", "OrganizationEnrichParams", "OrganizationHeadcountParams", "OrganizationOpportunitiesParams", "OrganizationResolveSlugParams", "OrganizationSimilarParams", "PeopleBatchEnrichParams", "PeopleProfileParams", "PeopleSearchParams", "PersonEmploymentHistoryParams", "PersonEndorsementsParams", "PersonEnrichParams", "PersonInterestsParams", "PersonLookalikesParams", "PersonResolveHandleParams", "ProspectsParams", "ReverseParams", "SkillsSearchParams", "SkillsSkillParams", "VerifyBatchParams", "VerifyParams"]
