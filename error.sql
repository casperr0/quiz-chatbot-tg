do $code$
declare
 ctx text;
begin
  raise sqlstate 'XR001';
  exception
    when sqlstate 'XR000' then
      raise notice 'XR000';
    when sqlstate 'XR001' then
      raise notice 'XR001';
end;
$code$
