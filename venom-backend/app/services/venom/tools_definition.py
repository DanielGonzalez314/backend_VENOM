def get_available_tools():
    """Devuelve la lista de herramientas para la IA (formato OpenAI)."""
    return [
        # === Herramientas existentes ===
        {
            "type": "function",
            "function": {
                "name": "generate_report_pdf",
                "description": "Genera un reporte en PDF con título y contenido.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "title": {"type": "string"},
                        "content": {"type": "string"}
                    },
                    "required": ["title", "content"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "web_search",
                "description": "Busca en internet usando Tavily.",
                "parameters": {
                    "type": "object",
                    "properties": {"query": {"type": "string"}},
                    "required": ["query"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "send_email",
                "description": "Envía un correo electrónico.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "to": {"type": "string"},
                        "subject": {"type": "string"},
                        "body": {"type": "string"}
                    },
                    "required": ["to", "subject", "body"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "process_file",
                "description": "Extrae texto de un archivo nuevo (en base64). NO usar para documentos del data lake.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "file_base64": {"type": "string"},
                        "filename": {"type": "string"}
                    },
                    "required": ["file_base64", "filename"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "translate_text",
                "description": "Traduce texto a otro idioma usando Gemini.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "text": {"type": "string"},
                        "target_lang": {"type": "string"},
                        "source_lang": {"type": "string"}
                    },
                    "required": ["text", "target_lang"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "generate_chart",
                "description": "Genera gráfico desde documento (usar document_id si ya subido).",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "document_id": {"type": "string"},
                        "file_base64": {"type": "string"},
                        "filename": {"type": "string"},
                        "x_column": {"type": "string"},
                        "y_column": {"type": "string"},
                        "chart_type": {"type": "string"},
                        "title": {"type": "string"}
                    },
                    "required": ["x_column", "y_column"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "compare_documents",
                "description": "Compara dos documentos (usar IDs si ya subidos).",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "doc1_id": {"type": "string"},
                        "doc2_id": {"type": "string"},
                        "doc1_base64": {"type": "string"},
                        "doc2_base64": {"type": "string"},
                        "doc1_name": {"type": "string"},
                        "doc2_name": {"type": "string"}
                    }
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "audit_conversation",
                "description": "Detecta datos sensibles en lista de mensajes.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "messages": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "role": {"type": "string"},
                                    "content": {"type": "string"}
                                }
                            }
                        }
                    },
                    "required": ["messages"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "list_documents",
                "description": "Lista documentos subidos en el data lake (IDs y nombres).",
                "parameters": {"type": "object", "properties": {}}
            }
        },
        # === Nuevas herramientas MCP individuales (explorer_*) ===
        {
            "type": "function",
            "function": {
                "name": "explorer_open",
                "description": "Abre el Explorador de Windows en una carpeta específica.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "path": {"type": "string", "description": "Ruta de la carpeta (ej. 'Documents' o 'C:/Program Files')."}
                    },
                    "required": ["path"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "explorer_list",
                "description": "Lista el contenido de un directorio.",
                "parameters": {
                    "type": "object",
                    "properties": {"path": {"type": "string"}},
                    "required": ["path"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "explorer_create_folder",
                "description": "Crea un nuevo directorio.",
                "parameters": {
                    "type": "object",
                    "properties": {"path": {"type": "string"}},
                    "required": ["path"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "explorer_create_file",
                "description": "Crea un archivo con contenido opcional.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "path": {"type": "string"},
                        "content": {"type": "string"}
                    },
                    "required": ["path"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "explorer_delete",
                "description": "Elimina un archivo o directorio.",
                "parameters": {
                    "type": "object",
                    "properties": {"path": {"type": "string"}},
                    "required": ["path"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "explorer_move",
                "description": "Mueve o renombra un archivo o directorio.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "source": {"type": "string"},
                        "destination": {"type": "string"}
                    },
                    "required": ["source", "destination"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "explorer_read",
                "description": "Lee el contenido de un archivo de texto.",
                "parameters": {
                    "type": "object",
                    "properties": {"path": {"type": "string"}},
                    "required": ["path"]
                }
            }
        },
        # === Otras MCP (música, apps, sistema, ventanas) ===
        {
            "type": "function",
            "function": {
                "name": "mcp_music",
                "description": "Control de música: play, add_to_queue, pause, resume, stop, next, status.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "action": {"type": "string", "enum": ["play", "add_to_queue", "pause", "resume", "stop", "next", "status"]},
                        "query": {"type": "string"}
                    },
                    "required": ["action"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "mcp_apps",
                "description": "Abre o cierra aplicaciones: start/kill.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "action": {"type": "string", "enum": ["start", "kill"]},
                        "app_name": {"type": "string"}
                    },
                    "required": ["action", "app_name"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "mcp_system",
                "description": "Estadísticas del sistema: stats (CPU/RAM/disco) o processes.",
                "parameters": {
                    "type": "object",
                    "properties": {"action": {"type": "string", "enum": ["stats", "processes"]}},
                    "required": ["action"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "mcp_windows",
                "description": "Control de ventanas: minimize, maximize, close, focus.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "action": {"type": "string", "enum": ["minimize", "maximize", "close", "focus"]},
                        "title": {"type": "string"}
                    },
                    "required": ["action", "title"]
                }
            }
        }
    ]