from gopy_machine import service;

svc = service.NewServices("2006-01-02");

data = service.Map_string_any();
# data.__setitem__("BSN", "999993653");

svc.EvaluateWithCtx("GEMEENTE_AMSTERDAM", "participatiewet/bijstand", data);