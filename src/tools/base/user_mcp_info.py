import os
import sys
import time
import subprocess
import platform
import mcp
from mcp.server.models import InitializationOptions
from mcp.types import ClientCapabilities, Implementation
import json
from typing import Optional

class UserMcpInfoTool():
    def __init__(self):
        pass

    def get_usetr_info(self) -> dict:

        # 1. Información del cliente
        client_info = {
            "timestamp": time.time(),
            "detection_methods": []
        }

        try:
            env_info = {

                "shell": os.getenv("SHELL", "Unknown"),
                "terminal": os.getenv("TERM", "Unknown"),
                "platform": platform.system(),
                "platform_release": platform.release(),
                "architecture": platform.machine(),
                "python_version": sys.version,
                "python_executable": sys.executable,
            }
            client_info["environment"] = env_info
            client_info["detection_methods"].append("environment_variables")
        except Exception as e:
            client_info["environment_error"] = str(e)
        
        # 2. Información del proceso
        try:
            current_pid = os.getpid()
            parent_pid = os.getppid()
            
            process_info = {
                "current_pid": current_pid,
                "parent_pid": parent_pid,
                "working_directory": os.getcwd(),
                "command_line_args": sys.argv,
            }
            
            # Intentar obtener comando del proceso padre
            try:
                if platform.system() != "Windows":
                    ps_cmd = f"ps -p {parent_pid} -o command --no-headers"
                    parent_command = subprocess.check_output(
                        ps_cmd, shell=True, text=True
                    ).strip()
                else:
                    # Windows
                    wmic_cmd = f'wmic process where processid={parent_pid} get commandline /value'
                    result = subprocess.check_output(wmic_cmd, shell=True, text=True)
                    parent_command = result.strip()
                
                process_info["parent_command"] = parent_command
            except:
                process_info["parent_command"] = "Unable to determine"
                
            client_info["process"] = process_info
            client_info["detection_methods"].append("process_information")
        except Exception as e:
            client_info["process_error"] = str(e)
        
        # 3. Análisis de stdio (común en MCP)
        try:
            stdio_info = {
                "stdin_isatty": sys.stdin.isatty(),
                "stdout_isatty": sys.stdout.isatty(),
                "stderr_isatty": sys.stderr.isatty(),
                "stdin_encoding": getattr(sys.stdin, 'encoding', 'Unknown'),
                "stdout_encoding": getattr(sys.stdout, 'encoding', 'Unknown'),
            }
            client_info["stdio"] = stdio_info
            client_info["detection_methods"].append("stdio_analysis")
        except Exception as e:
            client_info["stdio_error"] = str(e)
        
        # 4. Variables específicas de MCP/Claude
        try:
            mcp_vars = {
                k: v for k, v in os.environ.items() 
                if any(keyword in k.lower() for keyword in ['mcp', 'claude', 'anthropic', 'client'])
            }
            if mcp_vars:
                client_info["mcp_environment"] = mcp_vars
                client_info["detection_methods"].append("mcp_specific_vars")
        except Exception as e:
            client_info["mcp_vars_error"] = str(e)
        
        # 5. Inferir tipo de cliente
        try:
            client_type = "unknown"
            confidence = "low"
            
            # Análisis heurístico
            if "parent_command" in client_info.get("process", {}):
                parent_cmd = client_info["process"]["parent_command"].lower()
                
                if "claude" in parent_cmd:
                    client_type = "claude_desktop"
                    confidence = "high"
                elif "code" in parent_cmd or "vscode" in parent_cmd:
                    client_type = "vscode_extension"
                    confidence = "medium"
                elif "python" in parent_cmd:
                    client_type = "python_script"
                    confidence = "medium"
                elif "node" in parent_cmd or "npm" in parent_cmd:
                    client_type = "nodejs_application"
                    confidence = "medium"
                elif "curl" in parent_cmd or "wget" in parent_cmd:
                    client_type = "http_client"
                    confidence = "high"
            
            # Análisis de stdio
            if client_info.get("stdio", {}).get("stdin_isatty", False):
                if client_type == "unknown":
                    client_type = "interactive_terminal"
                    confidence = "medium"
            else:
                if client_type == "unknown":
                    client_type = "programmatic_client"
                    confidence = "low"
            
            client_info["inferred_client"] = {
                "type": client_type,
                "confidence": confidence
            }
            client_info["detection_methods"].append("heuristic_analysis")
            
        except Exception as e:
            client_info["inference_error"] = str(e)
        
        return client_info


class MCPClientDetector:
    def __init__(self):
        self.client_info = {}
        self.session_data = {}
        
    async def on_initialize(self, 
                          client_capabilities: ClientCapabilities,
                          client_info: Implementation,
                          initialization_options: Optional[InitializationOptions] = None):
        """Captura información del cliente durante la inicialización MCP"""
        
        # Información básica del cliente
        self.client_info = {
            "client_name": client_info.name if client_info else "Unknown",
            "client_version": client_info.version if client_info else "Unknown", 
            "protocol_version": "2024-11-05",  # Versión actual del protocolo MCP
            "initialization_time": time.time()
        }
        
        # Capacidades del cliente
        if client_capabilities:
            capabilities = {
                "experimental": getattr(client_capabilities, 'experimental', {}),
                "roots": getattr(client_capabilities, 'roots', None),
                "sampling": getattr(client_capabilities, 'sampling', None),
            }              
              
            self.client_info["capabilities"] = capabilities
        
        # Opciones de inicialización
        if initialization_options:
            self.client_info["initialization_options"] = {
                k: v for k, v in vars(initialization_options).items()
                if not k.startswith('_')
            }
        
        return self.client_info