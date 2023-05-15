# Extraction

Para lanzar la extracción hay que estar colocado en la raíz del proyecto y lanzar el siguiente comando:

    python extract/run.py -a  <activos>  -s <año inicio> -e <año fin> -o <formato de salida>

El script puede usar las siguientes flags:

| **Flag**                    | **Obligatorio** |                                         **Comentarios**                                          |        **Ejemplo**        |
|-----------------------------|:---------------:|:------------------------------------------------------------------------------------------------:|:-------------------------:|
| **-a, --assets, --activos** |       Si        | Listade activos. Tienen que estar separados por espacios y estar en el archivo de condfiguración | EURUSD,<br/>EURUSD EURAUD |
| **-s, --start, --inicio**   |       No        |                   Año de inicio. Si no se especifica se pondrá uno por defecto                   |           2017            |
| **-e, --end, --fin**        |       No        |                     Año de fin. Si no se especifica se pondrá el año actual                      |           2023            |
| **-o, --output**  |       No        |             Formato del archivo de salida. Si no se especifica se utilizará parquet              |       csv, parquet        |