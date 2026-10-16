> **ILUSTRATIVO – comprador ficticio – no constituye asesoramiento jurídico**

# 04b · Pliego de prescripciones técnicas (borrador ilustrativo)

## English summary

This is an **illustrative draft** of the technical specification (*pliego de prescripciones técnicas*, PPT) that a Spanish public hospital could publish to buy a pilot of an outbound voice-agent service for appointment confirmation and waiting-list backfill. The buyer is fictional (*Hospital General (fictional)*, part of a fictional regional health service). It is not legal advice and has not been reviewed by a procurement lawyer.

What it specifies:
- **Pilot lot:** one high no-show specialty, 90 days, compared with an SMS-only control arm.
- **Functions:** confirm, cancel and reschedule appointments; offer freed slots to the waiting list **strictly in the hospital's order**; hand off to a human; opt out of automated calls; Spanish and English at minimum.
- **No prioritisation:** the system never changes, scores or reorders the waiting list, which keeps it outside the AI Act Annex III high-risk use of deciding access to public healthcare.
- **Privacy and security:** processor contract (GDPR Art. 28), DPIA (Art. 35) signed off by the hospital's DPO, ENS (Real Decreto 311/2022), EU data residency, defined retention, identity check before any detail, callback number only on voicemail.
- **Transparency:** AI disclosure at the start of each call (AI Act Art. 50; application date to verify) and a recording notice.
- **Integration:** a narrow API; FHIR R4 `Appointment`/`Slot`/`Patient` as an option; batch files as a fallback.
- **Evidence:** a hash-chained record of recovered slots with a signed daily head handed to the hospital. **The hospital's booking system is the source of truth for billing**; the record is supporting evidence.
- **Price:** per verified recovered slot (filled by the agent, attended, matched to the hospital's booking, minus the SMS-arm baseline), with an optional small fixed fee and a hard cap below the *contrato menor* limit.
- **Acceptance criteria, kill switch and stop-loss**, suggested award criteria, and candidate CPV codes.

Business case and procurement routes: `docs/04_business_case.md`.

---

## Pliego de prescripciones técnicas para el servicio piloto de confirmación de citas y recuperación de huecos mediante agente de voz

**Órgano de contratación:** Hospital General (ficticio), servicio regional de salud (ficticio).
**Procedimiento previsto:** contrato menor de servicios (art. 118 de la Ley 9/2017, de Contratos del Sector Público, LCSP), precedido de consulta preliminar al mercado (art. 115 LCSP). Importe máximo inferior a 15.000 € (IVA excluido).
**Duración:** 90 días naturales de servicio, más un periodo previo de integración y pruebas de hasta 30 días.

### 1. Objeto

1.1. El objeto del contrato es la prestación de un servicio de llamadas salientes automatizadas, mediante un agente de voz, para:

a) confirmar, cancelar o reprogramar citas de consultas externas de atención especializada, con varios días de antelación;

b) ofrecer los huecos liberados a los pacientes de la lista de espera de la especialidad, **en el orden exacto que facilite el hospital**, hasta que el hueco se ocupe o deje de ser útil.

1.2. El servicio no incluye ninguna actividad asistencial. El agente no da consejo clínico, no valora la urgencia y no decide el acceso a la asistencia.

1.3. El indicador principal del servicio es el número de **huecos recuperados verificados** definido en el apartado 9.

### 2. Lote piloto

2.1. **Ámbito:** una única especialidad con alta tasa de inasistencia, que el hospital determinará antes del inicio a partir de sus propios datos.

2.2. **Diseño comparativo:** los pacientes citados en la especialidad se asignarán a dos grupos según el método que defina el hospital (aleatorización por paciente o por agenda):

| Grupo | Intervención |
|---|---|
| Control | Recordatorio por SMS habitual del hospital |
| Intervención | Recordatorio por SMS habitual + llamada del agente de voz y recuperación de huecos |

2.3. El adjudicatario no participa en la asignación de pacientes a los grupos ni puede alterarla.

2.4. **Volumen orientativo:** el hospital indicará el número estimado de citas del periodo. El adjudicatario dimensionará el servicio para atenderlas dentro de la ventana horaria del apartado 3.6.

### 3. Requisitos funcionales

3.1. **Confirmación.** El agente llamará al paciente con la antelación que fije el hospital (por defecto, entre 3 y 5 días antes de la cita), verificará su identidad y le pedirá que confirme la asistencia.

3.2. **Cancelación.** Si el paciente no puede acudir, el agente repetirá la fecha y hora de la cita y solo la cancelará tras una confirmación expresa del paciente. El hueco quedará liberado de inmediato en el sistema del hospital.

3.3. **Reprogramación.** El agente podrá ofrecer exclusivamente los huecos que devuelva el sistema del hospital. El cambio será atómico: el paciente conserva siempre una sola cita (la original o la nueva), también si la llamada se corta a mitad del proceso. El agente nunca inventará huecos.

3.4. **Recuperación de huecos.** Cuando se libere un hueco, el sistema llamará a los pacientes de la lista de espera de la especialidad **en el orden recibido del hospital**. El hueco quedará reservado para el paciente contactado durante un máximo de 10 minutos mientras decide; si no acepta, se ofrecerá al siguiente de la lista. Dos pacientes no podrán aceptar el mismo hueco.

3.5. **Lectura de confirmación.** Antes de cerrar cualquier cambio, el agente leerá al paciente la fecha, la hora y el lugar resultantes.

3.6. **Ventana de llamadas e intentos.** De lunes a sábado, de 9:00 a 20:00 (hora peninsular), salvo que el hospital indique otra. Como máximo 2 intentos por cita y día de campaña, y una sola llamada por cita y día.

3.7. **Transferencia a una persona.** El paciente podrá pedir hablar con una persona en cualquier momento. El agente transferirá la llamada al equipo de admisión en horario de atención o registrará una solicitud de devolución de llamada, con un resumen sin datos clínicos innecesarios.

3.8. **Baja de las llamadas automatizadas.** El paciente podrá pedir no recibir más llamadas automatizadas. La baja se registrará de inmediato, se comunicará al hospital y se respetará en todas las campañas siguientes. La baja no afecta a su cita ni a su posición en la lista.

3.9. **Preguntas clínicas.** Ante cualquier pregunta clínica (medicación, preparación, síntomas), el agente indicará que no puede responder y ofrecerá el contacto con el hospital. Ante una posible urgencia, indicará el teléfono de emergencias 112.

3.10. **Idiomas.** Español e inglés como mínimo. Se valorarán otros idiomas frecuentes en la población atendida (por ejemplo, rumano o árabe) y, en su caso, la lengua cooficial de la comunidad autónoma. El cambio de idioma durante la llamada no debe repetir la verificación de identidad ya superada.

3.11. **Accesibilidad.** Ritmo pausado, frases cortas y posibilidad de repetir la información, pensando en personas mayores o con dificultades auditivas.

3.12. **Panel de seguimiento.** El adjudicatario facilitará al equipo de admisión un panel con el estado de las llamadas, una cola de excepciones para atención humana con devolución de llamada, los huecos liberados y recuperados, y un interruptor de parada (apartado 11). El panel no se usará para medir el rendimiento individual del personal.

### 4. No priorización

4.1. El orden de la lista de espera es competencia exclusiva del hospital. El sistema **no puede crear, modificar, puntuar ni reordenar** la lista, ni saltarse a un paciente salvo por las causas objetivas que el hospital defina por escrito (por ejemplo, paciente que rechaza el hueco, que no contesta en los intentos previstos o que ha solicitado la baja).

4.2. El sistema **no libera huecos a partir de predicciones de inasistencia**. Un hueco solo se libera por cancelación del paciente o por decisión del personal del hospital.

4.3. Justificación: un sistema de IA que decidiera el orden de acceso a la asistencia sanitaria pública podría entrar en los usos de alto riesgo del anexo III del Reglamento (UE) 2024/1689 (Reglamento de Inteligencia Artificial). Este diseño mantiene la decisión en manos del hospital.

4.4. El adjudicatario conservará una instantánea de la lista recibida en cada campaña, de forma que pueda comprobarse que las ofertas siguieron ese orden (apartado 8).

### 5. Privacidad y seguridad

5.1. **Encargo de tratamiento.** El adjudicatario actuará como encargado del tratamiento y firmará el contrato del art. 28 del Reglamento (UE) 2016/679 (RGPD), con relación de subencargados, que el hospital deberá autorizar.

5.2. **Base jurídica.** Las llamadas son comunicaciones asistenciales del hospital con sus propios pacientes (arts. 6.1.e y 9.2.h RGPD; Ley Orgánica 3/2018, LOPDGDD; Ley 41/2002, de autonomía del paciente). No son comunicaciones comerciales.

5.3. **Evaluación de impacto.** El adjudicatario colaborará en la evaluación de impacto relativa a la protección de datos (EIPD, art. 35 RGPD) y aportará la información que le pida el delegado de protección de datos del hospital. El servicio no empezará sin la EIPD aprobada.

5.4. **Esquema Nacional de Seguridad.** El servicio cumplirá el ENS (Real Decreto 311/2022) en la categoría que determine el hospital (previsiblemente MEDIA, a confirmar), acreditado mediante certificación o declaración de conformidad según corresponda.

5.5. **Residencia de datos.** Los datos personales, grabaciones y transcripciones se tratarán y almacenarán en el Espacio Económico Europeo. Cualquier transferencia internacional requerirá autorización previa y garantías adecuadas.

5.6. **Minimización y conservación.** Solo se tratarán los datos necesarios: nombre, teléfono, fecha de nacimiento, parte del documento de identidad, idioma, cita y posición en la lista. El hospital fijará el plazo de conservación de grabaciones y transcripciones; a su término se suprimirán y se emitirá certificado. Se valorará la opción de no conservar datos en la plataforma de voz.

5.7. **Verificación de identidad antes de cualquier dato.** Antes de revelar cualquier información de la cita, incluida la especialidad, el agente verificará la identidad del paciente con al menos dos factores (por ejemplo, fecha de nacimiento y los tres últimos dígitos y la letra del documento de identidad). Tras 2 intentos fallidos en una llamada, la llamada termina con un número de devolución. Tras 3 llamadas fallidas en 24 horas, se bloquean las llamadas automatizadas a ese paciente y se avisa al personal. Todos los intentos quedan registrados.

5.8. **Buzón de voz y terceros.** Si contesta un buzón de voz o una persona distinta del paciente, el agente solo dejará el nombre del hospital y un número de devolución de llamada, sin ningún dato de salud ni de la cita.

5.9. **Seguridad de las integraciones.** Las llamadas del agente a las herramientas del adjudicatario estarán autenticadas con secreto compartido y con un identificador por llamada ligado a un único paciente; el sistema rechazará cualquier intento de consultar a otro paciente. Habrá límites de frecuencia y registro de rechazos.

5.10. **Registros técnicos.** Los registros de operación no contendrán datos de salud; se limitarán a identificadores seudónimos, herramienta, resultado y latencia.

5.11. **Incidentes.** El adjudicatario notificará al hospital cualquier violación de seguridad de los datos sin dilación indebida y, en todo caso, en un plazo máximo de 24 horas desde que tenga conocimiento, para que el hospital pueda cumplir el art. 33 RGPD.

### 6. Transparencia

6.1. **Aviso de IA.** Al inicio de cada llamada, el agente informará de que es un asistente automatizado que llama en nombre del hospital, conforme al art. 50 del Reglamento de Inteligencia Artificial (fecha de aplicación: 2 de agosto de 2026, **a verificar** antes de la publicación).

6.2. **Aviso de grabación.** Si la llamada se graba, el agente lo indicará al inicio, junto con la finalidad y el modo de ejercer los derechos.

6.3. **Texto de los avisos.** El hospital aprobará el texto exacto de ambos avisos en cada idioma.

### 7. Integración

7.1. El adjudicatario se integrará con el sistema de citación del hospital mediante una **interfaz estrecha** limitada a: consultar la cita, confirmar, cancelar, consultar huecos alternativos, reprogramar, consultar la lista de espera ordenada y registrar la asistencia.

7.2. **Opción preferente:** recursos HL7 FHIR R4 `Appointment`, `Slot` y `Patient` (subconjunto), si el sistema del hospital o su motor de integración los ofrece.

7.3. **Alternativa:** intercambio de ficheros por lotes cifrados (por ejemplo, citas y lista de espera diarias; resultados de vuelta) cuando no exista API, a través del motor de integración del hospital.

7.4. El adjudicatario no tendrá acceso a la historia clínica ni a ningún dato clínico distinto de la especialidad y la cita.

7.5. **Telefonía:** las llamadas saldrán de un número identificable del hospital o autorizado por él. El hospital indicará si deben usar su troncal SIP o centralita.

### 8. Registro de huecos recuperados

8.1. El adjudicatario mantendrá un **registro encadenado por hash** de todos los eventos del servicio (hueco liberado, ofertas, aceptaciones, verificaciones de identidad, asistencia), uno por hospital y día.

8.2. Cada día entregará al hospital la **cabecera firmada** (último hash de la cadena del día, con firma digital), que el hospital conservará fuera de los sistemas del adjudicatario. Con ella, el hospital o un auditor puede detectar si el registro se ha modificado después.

8.3. El adjudicatario facilitará una herramienta de verificación que compruebe la cadena, la firma, que las ofertas siguieron el orden de la lista recibida (apartado 4.4) y que no se reveló ningún dato antes de verificar la identidad.

8.4. **El sistema de citación del hospital es la fuente de verdad** para la facturación. El registro del adjudicatario es una prueba complementaria y no basta por sí solo para facturar un hueco.

### 9. Precio

9.1. **Hueco recuperado verificado.** Se considera facturable el hueco que cumple todas estas condiciones:

a) lo ha ocupado un paciente que lo aceptó en una llamada del agente;

b) el paciente asistió a la cita, según el sistema del hospital;

c) la cita figura en el sistema de citación del hospital para ese paciente y ese hueco.

9.2. **Línea base.** Del total anterior se descontará la tasa de recuperación de huecos observada en el grupo de control con solo SMS, aplicada a los huecos liberados en el grupo de intervención:

```
Huecos facturables = máx(0, huecos que cumplen 9.1 − tasa del grupo de control × huecos liberados en el grupo de intervención)
```

9.3. **Precio unitario:** el licitador ofertará un precio por hueco recuperado verificado.

9.4. **Cuota fija opcional:** el licitador podrá ofertar una cuota fija por integración y puesta en marcha, que computa dentro del importe máximo.

9.5. **Importe máximo:** la suma de la cuota fija y de los huecos facturables no superará el importe máximo del contrato, inferior a 15.000 € (IVA excluido). Superado ese importe, el servicio continúa sin coste adicional hasta el final del piloto o se detiene, a elección del hospital.

9.6. **Conciliación:** diaria y automática (registro del adjudicatario frente a la exportación de citas del hospital); factura mensual con la relación de huecos por identificador de hueco e identificador seudónimo del paciente, sin datos de salud. Los huecos en discrepancia no se facturan hasta resolverse.

9.7. No se facturan huecos de otras especialidades ni huecos ocupados mientras el servicio estuviera detenido por causa imputable al adjudicatario.

### 10. Criterios de aceptación

Antes del inicio (fase de pruebas, con datos sintéticos y llamadas solo a teléfonos de prueba autorizados por el hospital):

| # | Criterio | Umbral |
|---|---|---|
| A1 | Fugas de datos de salud a terceros o antes de verificar la identidad, en el conjunto de pruebas acordado | **0** |
| A2 | Aviso de IA al inicio de la llamada | En el 100 % de las llamadas de prueba |
| A3 | Lectura de confirmación antes de cada cambio | En el 100 % de los cambios de prueba |
| A4 | Ofertas de huecos en el orden de la lista recibida | 100 %, comprobado con la herramienta del apartado 8.3 |
| A5 | Ningún paciente con dos citas ni hueco asignado a dos pacientes | 0 casos en las pruebas de concurrencia |
| A6 | Rechazo de herramientas sin credencial o con identificador de otro paciente | 100 % |
| A7 | Transferencia a persona cuando se pide | Umbral a fijar por el hospital |
| A8 | Tiempo de respuesta de las herramientas (percentil 95) | Umbral a fijar por el hospital (referencia: 300 ms en servidor) |
| A9 | EIPD aprobada y contrato de encargo firmado | Requisito previo |

Durante el piloto, el hospital revisará semanalmente una muestra de llamadas y los indicadores de contacto, confirmación, cancelación anticipada, recuperación, transferencias e incidencias de privacidad. Los umbrales los fija el hospital; no se presuponen resultados.

### 11. Interruptor de parada y condiciones de detención

11.1. **Interruptor de parada.** El personal autorizado del hospital podrá detener todas las llamadas desde el panel en cualquier momento, con efecto inmediato sobre las llamadas nuevas. Quedará registrado quién lo activó y cuándo. Solo el hospital podrá reanudar el servicio.

11.2. **Detención automática** (sin perjuicio de otras que acuerden las partes):

a) cualquier fuga de datos de salud confirmada;

b) cualquier oferta de hueco fuera del orden de la lista;

c) un aumento anómalo de transferencias a persona o de quejas, según umbral fijado por el hospital;

d) errores de integración por encima del 5 % de las llamadas en una hora.

11.3. Tras una detención, el adjudicatario entregará en 48 horas un informe de causa y medidas, y el hospital decidirá la reanudación.

11.4. **Reversión.** El adjudicatario versionará la configuración del agente y podrá volver a la versión anterior aprobada en menos de una hora.

### 12. Criterios de adjudicación sugeridos (ilustrativos)

Para un procedimiento posterior al piloto (abierto o abierto simplificado). Las ponderaciones son **ilustrativas**; las fija el órgano de contratación.

| Criterio | Tipo | Peso ilustrativo |
|---|---|---|
| Precio por hueco recuperado verificado | Automático (fórmula) | 40 |
| Cuota fija y límite máximo | Automático (fórmula) | 10 |
| Diseño de privacidad y seguridad (verificación de identidad, residencia, conservación, ENS) | Juicio de valor | 20 |
| Calidad de la conversación y accesibilidad (personas mayores, idiomas) | Juicio de valor, con prueba práctica | 15 |
| Plan de integración y verificabilidad del registro de huecos | Juicio de valor | 10 |
| Plan de formación y acompañamiento al personal de admisión | Juicio de valor | 5 |

### 13. Códigos CPV candidatos

Propuestos como **candidatos**; el órgano de contratación decide.

| CPV | Descripción |
|---|---|
| 79512000 | Centro de llamadas (código principal propuesto) |
| 72000000 | Servicios TI: consultoría, desarrollo de software, Internet y apoyo |
| 48000000 | Paquetes de software y sistemas de información |
| 85100000 | Servicios de salud (solo si el órgano lo considera parte de la prestación asistencial; previsiblemente no aplica) |

---

> **ILUSTRATIVO – comprador ficticio – no constituye asesoramiento jurídico**
