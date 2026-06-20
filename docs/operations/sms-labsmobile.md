# SMS LabsMobile

## Variables

```text
SMS_ENABLED=false
LABSMOBILE_USER=
LABSMOBILE_TOKEN=
LABSMOBILE_TEST_MODE=true
LABSMOBILE_DEFAULT_MSISDN=52...
```

Con `SMS_ENABLED=false` se crea historial `Simulada` y no hay red. Con test mode activo el request real incluye `test: 1`. El endpoint es `https://api.labsmobile.com/json/send`, usa Basic Auth y envía `message` más `recipient: [{msisdn}]`. El token solo se lee del entorno.

`POST /api/v1/notifications/sms/test` exige `SMS_SEND`; `GET /api/v1/notifications/sms` lista historial. Estados: `Pendiente`, `Enviada`, `Fallida`, `Simulada`, `Cancelada`.

Al abrir una alerta de stock se crea como máximo un SMS para su `alerta_stock_id`. Si falta destinatario no se intenta. Si LabsMobile falla, la notificación queda `Fallida`, se audita y la operación que originó el movimiento continúa. Preflight emite warning si SMS está habilitado y faltan usuario, token o MSISDN.

QA debe ejecutarse primero con SMS deshabilitado. Las pruebas automatizadas inyectan transporte y nunca llaman internet.
