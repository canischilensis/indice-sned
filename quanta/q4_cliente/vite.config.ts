import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: { port: 5173, strictPort: true },

  /* El .env que gobierna al cliente es el de la raiz del repositorio, no uno
     propio de esta carpeta.

     Sin esta linea, Vite buscaba su .env aqui, no lo encontraba —nunca existio—
     y las direcciones venian de las constantes de reserva escritas en api.ts.
     Coincidian con lo intencionado por casualidad, de modo que el sistema
     funcionaba mientras nadie moviera un puerto. La configuracion declarada en
     .env.example para VITE_API_URL y VITE_AGENTE_URL no se leia jamas.

     Vite solo expone al navegador las variables con prefijo VITE_. El resto del
     archivo —claves, credenciales de base de datos, secreto de firma— no entra
     en el paquete. `tests/arquitectura/test_variables_del_cliente.py` verifica
     que ninguna variable con ese prefijo lleve nombre de secreto, porque esa
     garantia depende de una convencion de nombres y las convenciones se olvidan. */
  envDir: '../..',
})
