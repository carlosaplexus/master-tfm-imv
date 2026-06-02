

import http from "k6/http";
import { check, sleep } from "k6";

export const options = {
  tags: {
    imv: "Escenario_IMV_4"
  },  
  scenarios: {
    stress_test: {
      executor: "ramping-arrival-rate",
      startRate: 10,          // 10 req/min al inicio
      timeUnit: "1s",         // interpretamos rate como req/s
      preAllocatedVUs: 50,
      maxVUs: 1000,

      stages: [
        { target: 20, duration: "2m" },   // calentamiento: 20 req/s
        { target: 50, duration: "3m" },   // carga media
        { target: 100, duration: "3m" },  // carga alta
        { target: 150, duration: "3m" },  // muy alta
        { target: 200, duration: "3m" },  // zona roja
      ],
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

  check(res, {
    "status 201": (r) => r.status === 201,
  });

  sleep(1);
}
