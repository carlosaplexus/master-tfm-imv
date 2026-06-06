import http from "k6/http";
import { check, sleep } from "k6";

export const options = {
  tags: {
    imv: "Escenario_IMV_2"
  },  
  scenarios: {
    oleada1_initial: {
      executor: "constant-arrival-rate",
      rate: 20,               // 20 pacientes/minuto
      timeUnit: "1m",
      duration: "5m",
      preAllocatedVUs: 30,
      maxVUs: 100,
    },

    oleada2_rescue: {
      executor: "constant-arrival-rate",
      rate: 40,               // 40 pacientes/minuto
      timeUnit: "1m",
      duration: "10m",
      preAllocatedVUs: 50,
      maxVUs: 200,
      startTime: "5m",
    },

    oleada3_stabilization: {
      executor: "constant-arrival-rate",
      rate: 10,               // 10 pacientes/minuto
      timeUnit: "1m",
      duration: "15m",
      preAllocatedVUs: 20,
      maxVUs: 100,
      startTime: "15m",
    },
  },
};

function randomInt(min, max) {
  return Math.floor(Math.random() * (max - min + 1)) + min;
}

export default function () {
  const patient = {
    device_id: `dev-${__VU}-${Date.now()}`,       // único por VU con timestamp
    device_victim_seq: (__VU * 1000000) + __ITER,  // único por iteración
    //device_victim_seq: __ITER,

    Edad: randomInt(1, 90),
    Genero: Math.random() > 0.5 ? "M" : "F",

    LesionPrincipal: ["Trauma", "Quemadura", "Hemorragia", "Fractura"][randomInt(0, 3)],
    TriageAsignado: ["rojo", "amarillo", "verde", "negro"][randomInt(0, 3)],

    FrecuenciaCardiaca: randomInt(40, 160),
    FrecuenciaRespiratoria: randomInt(8, 40),
    PresionSistolica: randomInt(60, 180),
    Glasgow: randomInt(3, 15),
  };

  const headers = { "Content-Type": "application/json" };

  const res = http.post(
    "http://localhost:5001/api/patients",
    JSON.stringify(patient),
    { headers }
  );

  // check(res, {
  //   "status 201": (r) => r.status === 201,
  // });

  check(res, {
    "status 2xx": (r) => r.status >= 200 && r.status < 300,
  });

  sleep(1);
}


