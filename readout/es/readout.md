---
marp: true
theme: default
paginate: true
lang: es
title: "Slotback · Propuesta de piloto"
footer: "Hospital ficticio · datos sintéticos · los resultados simulados van etiquetados"
style: |
  section { font-family: "IBM Plex Sans", sans-serif; background: #FBFAF7; color: #1B1A17; font-size: 26px; }
  h1, h2 { color: #1B1A17; font-weight: 600; }
  strong { color: #1F5FA8; }
  code, .num { font-family: "IBM Plex Mono", monospace; }
  .sim { background: #FFE7A8; color: #6B4A00; font-family: "IBM Plex Mono", monospace; font-size: 16px; padding: 2px 6px; border-radius: 2px; }
  .bench { border: 1px solid #3D5A78; color: #3D5A78; font-family: "IBM Plex Mono", monospace; font-size: 16px; padding: 1px 6px; border-radius: 2px; }
  .synth { border: 1px solid #5E5A52; color: #5E5A52; font-family: "IBM Plex Mono", monospace; font-size: 16px; padding: 1px 6px; border-radius: 2px; }
  .care { border: 1px solid #1F6F60; color: #1F6F60; font-size: 18px; padding: 1px 6px; border-radius: 2px; }
  table { font-size: 22px; }
  footer { font-size: 14px; color: #5E5A52; }
---

# Huecos recuperados, no recordatorios

**Propuesta de piloto de 90 días para Consultas Externas**
Hospital General (ficticio) · Dirección Gerencia

Asistente de voz que confirma citas y ofrece los huecos liberados a la lista de espera, **en el orden que fija el hospital**.

<span class="sim">SIMULADO</span> Todos los resultados de Slotback de este documento proceden de una jornada sintética. Todavía no se ha hecho ningún piloto real.

---

## 1 · El problema: consultas que nadie aprovecha

| Referencia (otras regiones) | Dato | Fuente |
|---|---|---|
| Área sanitaria, consultas externas | **13,8 %** de 400.761 citas perdidas; **≈ 3,39 M€** | <span class="bench">BENCHMARK [S2, 2013–14]</span> |
| Comunidad Valenciana, consultas especializadas | **9,7 %**: 733.580 de 7,56 M | <span class="bench">BENCHMARK [S1, 2014]</span> |
| Galicia, consultas hospitalarias | **5,75 %**: 245.535 perdidas | <span class="bench">BENCHMARK [S5, 2024]</span> |

- Coste medio de una cita perdida: **≈ 61 €** <span class="bench">BENCHMARK [S2, 2013–14]</span> (cálculo propio).
- Para el Hospital General (ficticio): 380.000 citas al año, 12 % de inasistencia → **≈ 45.600 huecos vacíos** <span class="synth">SINTÉTICO</span>

---

## 2 · Por qué faltan los pacientes

- **29,6 %** se olvidó; **16 %** fallo de comunicación con el centro → **46 %** entre los dos <span class="bench">BENCHMARK [S2, 2013–14]</span>
- Quienes faltan son algo más jóvenes (51,3 frente a 55,7 años) y esperaron más desde la citación (25,2 frente a 19,2 días) <span class="bench">[S2]</span>. Son asociaciones, no predicciones.
- Las líneas telefónicas para anular están saturadas; la defensoría regional señala que afecta más a mayores y a zonas rurales <span class="bench">[S3, 2021]</span>.

**Lo que ya funciona:** el SMS es la medida más coste-efectiva contra el olvido [S2]. No proponemos sustituirlo.

---

## 3 · Lo que el SMS no puede hacer

| | SMS | SMS + asistente de voz |
|---|---|---|
| Recordar la cita | ✓ | ✓ |
| Anular o cambiar la cita en la misma llamada | ✕ | ✓ |
| Ofrecer el hueco liberado al siguiente de la lista **hoy** | ✕ | ✓ |
| Detectar teléfonos desactualizados [S5] | ✕ | ✓ |
| Atender a quien no lee SMS o prefiere hablar | ✕ | ✓ |

El valor no es "un recordatorio mejor": es **convertir una ausencia en una anulación a tiempo, y esa anulación en una cita para otro paciente.**

---

## 4 · Cómo funciona

1. **3–5 días antes**, el asistente llama: se presenta como asistente automático, avisa de la grabación y **verifica la identidad** (fecha de nacimiento + parte del DNI) antes de decir nada, ni siquiera la especialidad.
2. El paciente **confirma, anula o cambia** la cita. Se le lee de vuelta lo acordado.
3. Si se libera un hueco, el asistente llama a la lista de espera **estrictamente en el orden del hospital**, con 10 minutos de reserva por oferta.
4. Buzón de voz o un familiar: **solo un número para devolver la llamada**, sin datos de salud.
5. Cualquier duda clínica, petición de hablar con una persona o caso delicado → **personal de Admisión**.

<span class="care">◆ IA identificada</span> <span class="care">◆ identidad verificada</span> <span class="care">◆ lectura de confirmación</span> <span class="care">◆ paso a una persona</span>

---

## 5 · Resultados en la jornada sintética

<span class="sim">SIMULADO</span> Jornada sintética: 5 especialidades, 400 citas, 60 pacientes por lista de espera. No son resultados reales.

| Indicador | Valor |
|---|---|
| Huecos recuperados | <!--m:recovered_slots-->14<!--/m--> <span class="sim">SIMULADO</span> |
| De ellos, facturables (acudió + cuadra con la agenda del hospital − línea base SMS) | <!--m:billable_recovered_slots-->9<!--/m--> <span class="sim">SIMULADO</span> |
| Tasa de cobertura de huecos liberados | <!--m:fill_rate-->100%<!--/m--> <span class="sim">SIMULADO</span> |
| Mediana hasta cubrir el hueco (min) | <!--m:median_time_to_fill_min-->11.0<!--/m--> <span class="sim">SIMULADO</span> |
| Fugas de datos en <!--m:eval_scenarios_total-->15<!--/m--> conversaciones de prueba | <!--m:privacy_leaks-->0<!--/m--> <span class="sim">SIMULADO</span> |
| Coste por hueco recuperado (€) | <!--m:cost_per_recovered_slot_eur-->€3.54<!--/m--> <span class="sim">SIMULADO</span> |

Cada hueco queda en un **registro encadenado** con cabecera diaria firmada que se entrega al hospital. La agenda del hospital sigue siendo la fuente de verdad.

---

## 6 · Riesgos y cómo se controlan

| Riesgo | Control |
|---|---|
| Revelar datos de salud a otra persona | Identidad antes de cualquier dato; buzón y terceros: solo número de contacto; detector de fugas con tolerancia cero |
| Que la IA decida quién se atiende antes | **Nunca prioriza.** Ofrece en el orden de la lista del hospital; los huecos solo se liberan por anulación o por el personal. Queda fuera del anexo III del Reglamento de IA |
| Consejo clínico | Prohibido; deriva a una persona o al 112 |
| Rechazo de pacientes mayores | Ritmo pausado, opción de deletrear cifras, paso a una persona siempre disponible |
| Algo va mal en producción | **Interruptor de parada** en consola, con registro de quién y cuándo; paradas automáticas por umbral |

Base jurídica: RGPD art. 6.1.e y 9.2.h, LOPDGDD, Ley 41/2002. Encargo de tratamiento (art. 28), EIPD (art. 35), ENS. Transparencia del Reglamento de IA, art. 50 (fecha de aplicación: pendiente de verificar).

---

## 7 · El piloto: 90 días, una especialidad

- **Una especialidad** con alta inasistencia y lista de espera exportable en orden.
- **Grupo control:** solo SMS (lo de hoy). **Grupo intervención:** SMS + asistente de voz. Asignación por día de consulta.
- Semana 2 en **modo sombra** (propone, no llama); semana 3 arranque reducido; reprogramación a partir de la semana 7.
- Plan de análisis cerrado **antes** de empezar.

| Decisión al día 90 | Se sigue si… |
|---|---|
| Privacidad | Cero revelaciones confirmadas |
| Orden de la lista | Cero ofertas fuera de orden |
| Huecos facturables | Por encima del umbral que fije la Dirección |
| Aceptación | Bajas y quejas por debajo del umbral pactado con Atención al Paciente |

---

## 8 · Propuesta económica y vía de contratación

**Se paga por hueco recuperado verificado**: cubierto por el asistente, **con asistencia del paciente**, **cuadrado con la agenda del hospital**, y descontando lo que el grupo SMS habría cubierto igualmente.

| Opción | Riesgo para el hospital | Riesgo para el proveedor |
|---|---|---|
| Por minuto | Alto: paga aunque no haya resultado | Bajo |
| Por hueco recuperado verificado, con tope | Bajo | Alto (**recomendada para el piloto**) |
| Cuota fija pequeña + importe por hueco | Moderado | Moderado (**recomendada al escalar**) |

**Vía:** consulta preliminar al mercado → **contrato menor** para el piloto (servicios < 15.000 € sin IVA, LCSP 9/2017) → procedimiento abierto o asociación para la innovación para escalar. Borrador de pliego disponible.

---

## 9 · Lo que pedimos

1. **Autorizar el piloto** de 90 días en una especialidad, con SMS como grupo control.
2. **Designar** a la jefa o jefe de Admisión como responsable del servicio.
3. **Iniciar con la DPD** la revisión del borrador de EIPD, y **consultar al comité de empresa** antes del arranque.
4. **Encargar a Sistemas** la exportación diaria de la lista de espera en su orden oficial.
5. **Fijar los umbrales** de continuidad del día 90 antes de empezar.

Próximo paso: reunión de 45 minutos con Admisión, Sistemas y la DPD en las dos próximas semanas.

---

## Fuentes

Todas comprobadas en los documentos originales el 16-10-2026. Las instituciones se describen de forma genérica.

- **[S1]** Nota de prensa sobre inasistencia en consultas especializadas, Comunidad Valenciana, ene–nov 2014 (publicada 30-01-2015).
- **[S2]** Jabalera Mesa, M.L. (2015). *Factores determinantes del absentismo en consultas externas*, tesis doctoral, datos 2013–14 (tablas 26, 29 y 46).
- **[S3]** Resolución de una defensoría regional, expediente 1259/2021 (atención primaria).
- **[S5]** Nota de prensa sobre inasistencia en Galicia en 2024 (publicada 28-01-2025).

Detalle: `docs/01_account_brief.md` y `research/sources.md`. Resultados de Slotback: `metrics/registry.json`, todos **SIMULADOS**.
