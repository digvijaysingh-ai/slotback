# Nota para Dirección Gerencia · Piloto Slotback

**Para:** Dirección Gerencia, Hospital General (ficticio)
**Asunto:** piloto de 90 días de un asistente de voz para confirmar citas y recuperar huecos de Consultas Externas
**Fecha:** 16-10-2026
**Aviso:** hospital ficticio y datos sintéticos. Las cifras públicas son referencias de otras regiones, con su fuente y año. Los resultados de Slotback son **SIMULADOS**: no se ha hecho ningún piloto real.

---

**1. Problema.** En otras regiones se pierden entre el 5,75 % y el 14,6 % de las citas de consultas especializadas (Galicia 2024 [S5]; un hospital de tercer nivel, 2011 [S6]). En el área mejor documentada fue el 13,8 %, unos 3,39 M€ al año y unos 61 € por cita perdida (tesis doctoral, datos 2013–14 [S2]). El 46 % de quienes faltaron dijeron que se olvidaron o que hubo un fallo de comunicación [S2]. Con el perfil sintético del hospital (380.000 citas, 12 %), serían unos 45.600 huecos vacíos al año (SINTÉTICO).

**2. Qué proponemos.** Un asistente de voz que llama 3–5 días antes de la cita para confirmarla, anularla o cambiarla, y que ofrece cada hueco liberado a la lista de espera **en el orden que fija el hospital**, con una reserva de 10 minutos por oferta. No sustituye al SMS, que es la medida más barata contra el olvido [S2]: hace lo que el SMS no puede, que es recoger la anulación y dar el hueco a otro paciente antes del día.

**3. Garantías.** Se identifica como asistente automático y avisa de la grabación. Verifica la identidad antes de dar cualquier dato, incluida la especialidad. En buzones de voz o con terceros deja solo un número de contacto. Nunca da consejo clínico ni decide prioridades; los huecos solo se liberan por anulación o por el personal, lo que lo deja fuera del anexo III del Reglamento de IA. Siempre se puede pedir hablar con una persona o darse de baja. Hay un interruptor de parada en la consola.

**4. Resultados simulados.** En una jornada sintética (5 especialidades, 400 citas): <!--m:recovered_slots-->14<!--/m--> huecos recuperados, <!--m:billable_recovered_slots-->9<!--/m--> facturables y <!--m:privacy_leaks-->0<!--/m--> fugas de datos en <!--m:eval_scenarios_total-->15<!--/m--> conversaciones de prueba. Todo **SIMULADO**. Sirven para mostrar el método, no para prometer un resultado.

**5. Piloto.** 90 días en una especialidad con alta inasistencia. Grupo control solo SMS; grupo intervención SMS + voz, asignado por día de consulta. Modo sombra en la semana 2. Se continúa solo si hay cero revelaciones de datos, cero ofertas fuera de orden y los huecos facturables superan el umbral que fije Dirección antes de empezar.

**6. Precio y contratación.** Se paga por **hueco recuperado verificado**: cubierto por el asistente, con asistencia del paciente, cuadrado con la agenda del hospital, y descontando lo que el grupo SMS habría cubierto igualmente. Importe total con tope, dentro de un **contrato menor** (servicios < 15.000 € sin IVA, LCSP 9/2017). Para escalar: procedimiento abierto o asociación para la innovación.

**7. Decisiones que pedimos.** (a) Autorizar el piloto. (b) Designar a Admisión como responsable. (c) Abrir la revisión de la EIPD con la DPD y consultar al comité de empresa. (d) Pedir a Sistemas la exportación diaria de la lista de espera en su orden. (e) Fijar los umbrales del día 90.

---

*Fuentes: [S2] Jabalera Mesa (2015), tesis doctoral, datos 2013–14; [S5] nota de prensa sobre Galicia, datos 2024; [S6] Pereira-Victorio et al. (2016), datos 2011. Detalle en `docs/01_account_brief.md`.*
