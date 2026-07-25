export type Exercise = {
  id: string;
  name: string;
  shortDescription: string;
  description: string;
  muscles: string[];
  difficulty: "Principiante" | "Intermedio" | "Avanzado";
  tips: string[];
  available: boolean;
};

export const exercises: Exercise[] = [
  {
    id: "sentadillas",
    name: "Sentadillas",
    shortDescription: "Fuerza de piernas y control de cadera.",
    description:
      "La sentadilla es el ejercicio base para tren inferior: baja controlando la cadera hacia atrás y abajo, manteniendo el torso erguido, hasta que el muslo quede paralelo al piso.",
    muscles: ["Cuádriceps", "Glúteos", "Core"],
    difficulty: "Principiante",
    tips: [
      "Separa los pies al ancho de los hombros.",
      "Baja empujando la cadera hacia atrás, como si te sentaras.",
      "Mantén el pecho arriba y la espalda neutra.",
      "Las rodillas siguen la dirección de los pies, sin colapsar hacia adentro.",
    ],
    available: true,
  },
  {
    id: "desplantes",
    name: "Desplantes",
    shortDescription: "Estabilidad unilateral y fuerza de piernas.",
    description:
      "El desplante (o zancada) trabaja cada pierna por separado: das un paso adelante y bajas hasta que ambas rodillas queden cerca de 90°, cuidando que la rodilla delantera no pase la punta del pie.",
    muscles: ["Cuádriceps", "Glúteos", "Isquiotibiales"],
    difficulty: "Intermedio",
    tips: [
      "Da un paso largo hacia adelante antes de bajar.",
      "Baja en línea recta, sin que la rodilla se vaya hacia adentro.",
      "Mantén el torso vertical durante todo el movimiento.",
      "Alterna de pierna entre repeticiones para trabajar ambos lados.",
    ],
    available: true,
  },
  {
    id: "curl-biceps",
    name: "Curl de bíceps",
    shortDescription: "Fuerza de brazo, aislando el bíceps.",
    description:
      "El curl de bíceps flexiona el codo llevando la mano hacia el hombro. Todo el movimiento pasa por el codo: el hombro se mantiene quieto y pegado al cuerpo durante toda la repetición.",
    muscles: ["Bíceps", "Antebrazo"],
    difficulty: "Principiante",
    tips: [
      "Ubícate de frente a la cámara, a la altura de la cintura para arriba.",
      "Mantén el codo pegado al torso durante todo el movimiento.",
      "Sube controlando, sin usar impulso del hombro ni de la espalda.",
      "Baja completo antes de empezar la siguiente repetición.",
    ],
    available: true,
  },
  {
    id: "elevaciones-laterales",
    name: "Elevaciones laterales",
    shortDescription: "Aislamiento de hombro (deltoides lateral).",
    description:
      "Las elevaciones laterales levantan los brazos hacia los costados hasta la altura del hombro. Es un movimiento controlado: subir rápido o pasarse de altura suele significar que está entrando el trapecio en vez del hombro.",
    muscles: ["Hombros", "Deltoides"],
    difficulty: "Intermedio",
    tips: [
      "Ubícate de frente a la cámara, a la altura de la cintura para arriba.",
      "Sube los brazos hasta la altura del hombro, no más arriba.",
      "Controla la bajada, no dejes caer los brazos.",
      "Evita encoger los hombros hacia las orejas al subir.",
    ],
    available: true,
  },
  {
    id: "flexiones",
    name: "Flexiones",
    shortDescription: "Empuje de tren superior y core.",
    description:
      "Próximamente vas a poder practicar flexiones de brazos con corrección de forma en tiempo real, igual que con el resto de los ejercicios.",
    muscles: ["Pecho", "Tríceps", "Core"],
    difficulty: "Intermedio",
    tips: [],
    available: false,
  },
  {
    id: "plancha",
    name: "Plancha",
    shortDescription: "Estabilidad de core e isometría.",
    description:
      "Próximamente vas a poder practicar la plancha con seguimiento de alineación de cadera y espalda en tiempo real.",
    muscles: ["Core", "Espalda baja", "Hombros"],
    difficulty: "Principiante",
    tips: [],
    available: false,
  },
];

export function getExerciseById(id: string): Exercise | undefined {
  return exercises.find((exercise) => exercise.id === id);
}
