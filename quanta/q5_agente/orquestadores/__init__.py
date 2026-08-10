"""Adaptadores del puerto `AsesorDeGestion`.

`AgenteDeBucleSimple` vive en `q5_agente/bucle.py` y no depende de nada fuera de
`httpx`. Este paquete alberga los que si traen una pila propia.

Nada se importa aqui a proposito. La fabrica los carga de forma perezosa, igual
que hace con los SDK de los proveedores externos: asi la consola sigue
arrancando sin `pydantic` ni `langchain`, y la prueba que lo verifica —
`tests/arquitectura/`— no necesita excepciones.
"""
