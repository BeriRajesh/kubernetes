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

insert into @temp EXEC AN_person_project_eid_access_v1 @is_return_roles=1;


Select Distinct p.name, p.email, p.company, p.country,  t.PersonGUID from @temp t
  LEFT JOIN Person p on p.personGUID = t.PersonGUID
where t.projectguid in (select guid_project from an_project_v2 where guid_client  in ('BAFE4134-45A1-49EA-8DA0-50626F44A24B', 'EA1D8569-56C7-4E15-9B18-B1A8B5A2072D'))
and t.personGUID in (Select Distinct t2.PersonGUID from @temp t2
where t2.projectguid in (select guid_project from an_project_v2 where guid_client  = 'A525F152-4BBC-11E7-A993-0A75EE8C1078'))
set nocount off
