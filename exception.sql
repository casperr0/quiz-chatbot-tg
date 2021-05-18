do $code$
 begin
  begin
    update atable set col=val where pk=pk_val;
    raise exception 'exception';
  exception
   when others then null;
  end;
  raise notice 'we are here';
end;
$code$
