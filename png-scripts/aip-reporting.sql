use empowerID

set nocount on

Declare @temp table
(
PersonID int,
ResourceID int,
PersonGUID uniqueidentifier,
ProjectGUID uniqueidentifier,
RoleList varchar(100)
);

insert into @temp EXEC AN_person_project_eid_access_v1  @is_return_roles=1

Select t.personguid as "PersonGUID", p.name as "Person Name", p.login as "UserID", p.company as "Person Company", p.email as "Person Email", p.country as "Person Country", ap.guid_client as "Client GUID", ac.org_name as "Client Name",t.ProjectGUID as "ProjectGUID", ap.project_name as "Project Name", ap.type_key as "Project Type", t.rolelist as "Project Role" 
from @temp t, Person p, an_project_v2 ap, an_client ac
where p.personguid = t.PersonGUID
and ap.guid_project = t.ProjectGUID
and ap.guid_client = ac.guid_client
and ap.type_key in ('assembly', 'dataviz', 'analyze', 'ade_catalog')
and p.email like '%@pg.com%'

set nocount off
