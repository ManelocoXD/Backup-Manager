# 🛡️ SmartBackup

<div align="center">

![SmartBackup](https://img.shields.io/badge/SmartBackup-v1.0-blue?style=for-the-badge)
![Platform](https://img.shields.io/badge/Platform-Windows-0078D6?style=for-the-badge&logo=windows)
![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)

**Una aplicación moderna y elegante para realizar copias de seguridad de tus archivos**

[Características](#-características) • [Instalación](#-instalación) • [Uso](#-uso) • [Programación](#-programación) • [Desarrollo](#-desarrollo)

</div>

---

## ✨ Características

- 📦 **Backup Completo** - Copia todos los archivos de la carpeta origen
- ⚡ **Backup Incremental** - Solo copia archivos nuevos o modificados desde el último backup
- 📈 **Backup Diferencial** - Copia archivos modificados desde el último backup completo
- 📅 **Programación** - Programa backups automáticos (diario, semanal, mensual, personalizado)
- 🌐 **Bilingüe** - Interfaz en español e inglés
- 🎨 **Tema Automático** - Se adapta al tema claro/oscuro de tu sistema
- 💻 **Portable** - No requiere instalación, ejecutable independiente

## 📥 Instalación

### Opción 1: Descargar Ejecutable (Recomendado)

1. Ve a la sección [Releases](../../releases)
2. Descarga `SmartBackup.exe`
3. Ejecuta directamente - ¡No requiere instalación!

### Opción 2: Ejecutar desde Código Fuente

```bash
# Clonar el repositorio
git clone https://github.com/tu-usuario/SmartBackup.git
cd SmartBackup

# Crear entorno virtual
python -m venv venv

# Activar entorno virtual
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# Instalar dependencias
pip install -r requirements.txt

# Ejecutar
python main.py
```

### Opción 3: Compilar tu Propio Ejecutable

```bash
# Después de la Opción 2, ejecutar:
python build.py
```
El ejecutable se creará en la carpeta `dist/`

## 🚀 Uso

### Realizar un Backup Manual

1. **Seleccionar Origen** - Haz clic en "Explorar" junto a "Carpeta Origen" y selecciona la carpeta que quieres respaldar
2. **Seleccionar Destino** - Haz clic en "Explorar" junto a "Carpeta Destino" y selecciona dónde guardar el backup
3. **Elegir Modo**:
   - 💾 **Completo**: Copia todo (ideal para primer backup)
   - 📊 **Incremental**: Solo cambios desde el último backup (rápido, ahorra espacio)
   - 📈 **Diferencial**: Cambios desde el último backup completo
4. **Iniciar** - Clic en "🚀 Backup Ahora"

### Barra de Progreso

Durante el backup verás:
- Barra de progreso visual
- Contador de archivos procesados
- Archivo actual siendo copiado

## 📅 Programación

SmartBackup permite programar backups automáticos:

1. Clic en "📅 Programar" en la esquina superior derecha
2. Clic en "✨ Añadir Programación"
3. Configurar:
   - **Nombre**: Identificador para esta programación
   - **Origen/Destino**: Carpetas a respaldar
   - **Modo**: Tipo de backup
   - **Frecuencia**: 
     - Una vez
     - Cada hora (configurable)
     - Diario
     - Semanal
     - Mensual
     - Personalizado (elegir días específicos)
   - **Hora**: Cuándo ejecutar
4. Clic en "💾 Guardar"

### Gestión de Programaciones

En la lista de programaciones puedes:
- ▶️ Ejecutar ahora
- ✏️ Editar configuración
- 🗑️ Eliminar programación

## 📁 Estructura del Backup

```
📂 Destino/
├── 📁 backup_YYYYMMDD_HHMMSS/    # Backup completo
│   └── (copia de todos los archivos)
├── 📁 incremental_YYYYMMDD_HHMMSS/    # Backup incremental
│   └── (solo archivos nuevos/modificados)
└── 📁 differential_YYYYMMDD_HHMMSS/   # Backup diferencial
    └── (cambios desde último completo)
```

## ⚙️ Configuración

La configuración se guarda automáticamente en:
- **Windows**: `%APPDATA%/SmartBackup/config.json`

Incluye:
- Última carpeta origen/destino usada
- Modo de backup preferido
- Idioma (auto/es/en)
- Tema (auto/light/dark)
- Programaciones guardadas

## 🛠️ Desarrollo

### Requisitos

- Python 3.10+
- customtkinter
- pillow

### Estructura del Proyecto

```
SmartBackup/
├── main.py              # Punto de entrada
├── build.py             # Script de compilación
├── requirements.txt     # Dependencias
├── smartbackup/
│   ├── __init__.py
│   ├── config.py        # Gestión de configuración
│   ├── backup_engine.py # Motor de backup
│   ├── scheduler.py     # Programador de tareas
│   ├── locales.py       # Traducciones
│   └── ui/
│       ├── main_window.py    # Ventana principal
│       ├── schedule_dialog.py # Diálogo de programación
│       ├── help_dialog.py    # Diálogo de ayuda
│       └── theme.py          # Gestión de temas
└── resources/
    └── icon.png         # Icono de la aplicación
```

### Contribuir

1. Fork el repositorio
2. Crea una rama (`git checkout -b feature/nueva-caracteristica`)
3. Commit tus cambios (`git commit -m 'Añadir nueva característica'`)
4. Push a la rama (`git push origin feature/nueva-caracteristica`)
5. Abre un Pull Request

## 📄 Licencia

Este proyecto está bajo la Licencia MIT - ver el archivo [LICENSE](LICENSE) para más detalles.

---

<div align="center">

**¿Te gusta SmartBackup?** ⭐ ¡Dale una estrella al repositorio!

Hecho con ❤️ usando Python y CustomTkinter

</div>
