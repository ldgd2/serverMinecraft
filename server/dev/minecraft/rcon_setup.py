"""
dev/minecraft/rcon_setup.py
Configurador interactivo de RCON — selección de servidor por lista.
"""
import typer
import os
import glob
import secrets
import string
import socket
import struct
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.prompt import Prompt, Confirm
from rich import box
from rich.text import Text

app = typer.Typer(help="Configurar RCON para comunicación App ↔ Minecraft")
console = Console()

# ─── Rutas base ───────────────────────────────────────────────────────────────
_HERE        = os.path.dirname(os.path.abspath(__file__))
_SERVER_ROOT = os.path.abspath(os.path.join(_HERE, "..", ".."))
ENV_FILE     = os.path.join(_SERVER_ROOT, ".env")
SERVERS_DIR  = os.path.join(_SERVER_ROOT, "servers")
RCON_PORT    = 25575
RCON_HOST    = "127.0.0.1"


# ─── Helpers ──────────────────────────────────────────────────────────────────

def _gen_password(length: int = 24) -> str:
    alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
    return ''.join(secrets.choice(alphabet) for _ in range(length))


def _read_env() -> dict:
    env = {}
    if not os.path.exists(ENV_FILE):
        return env
    with open(ENV_FILE, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, _, v = line.partition("=")
            env[k.strip()] = v.strip()
    return env


def _write_env(env: dict):
    lines = [f"{k}={v}\n" for k, v in env.items()]
    with open(ENV_FILE, "w", encoding="utf-8") as f:
        f.writelines(lines)


def _read_rcon_from_props(props_path: str) -> dict:
    """Lee las claves RCON de un server.properties."""
    result = {"enable-rcon": "false", "rcon.port": "", "rcon.password": ""}
    if not os.path.exists(props_path):
        return result
    with open(props_path, "r", encoding="utf-8", errors="replace") as f:
        for line in f:
            key = line.strip().split("=", 1)[0]
            val = line.strip().split("=", 1)[-1] if "=" in line else ""
            if key in result:
                result[key] = val
    return result


def _patch_props(props_path: str, password: str, port: int) -> bool:
    """Escribe enable-rcon, rcon.port y rcon.password en server.properties."""
    if not os.path.exists(props_path):
        return False
    with open(props_path, "r", encoding="utf-8", errors="replace") as f:
        lines = f.readlines()

    found = {"enable-rcon": False, "rcon.port": False, "rcon.password": False}
    new_lines = []
    for line in lines:
        key = line.strip().split("=", 1)[0]
        if key == "enable-rcon":
            new_lines.append(f"enable-rcon=true\n")
            found["enable-rcon"] = True
        elif key == "rcon.port":
            new_lines.append(f"rcon.port={port}\n")
            found["rcon.port"] = True
        elif key == "rcon.password":
            new_lines.append(f"rcon.password={password}\n")
            found["rcon.password"] = True
        else:
            new_lines.append(line)

    if not found["enable-rcon"]:
        new_lines.append(f"enable-rcon=true\n")
    if not found["rcon.port"]:
        new_lines.append(f"rcon.port={port}\n")
    if not found["rcon.password"]:
        new_lines.append(f"rcon.password={password}\n")

    with open(props_path, "w", encoding="utf-8") as f:
        f.writelines(new_lines)
    return True


def _rcon_test(host: str, port: int, password: str, timeout: float = 3.0):
    """Devuelve (ok: bool, mensaje: str)."""
    try:
        def build(pid, ptype, payload):
            body = (payload + "\x00\x00").encode("utf-8")
            length = 4 + 4 + len(body)
            return struct.pack("<iii", length, pid, ptype) + body

        def read_pkt(s):
            raw = s.recv(4)
            if not raw:
                raise ConnectionError("Sin datos")
            length = struct.unpack("<i", raw)[0]
            data = b""
            while len(data) < length:
                chunk = s.recv(length - len(data))
                if not chunk:
                    raise ConnectionError("Conexión cerrada")
                data += chunk
            pid, ptype = struct.unpack("<ii", data[:8])
            payload = data[8:-2].decode("utf-8", errors="replace")
            return pid, ptype, payload

        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(timeout)
            s.connect((host, port))
            s.sendall(build(1, 3, password))
            pid, _, _ = read_pkt(s)
            if pid == -1:
                return False, "Contraseña incorrecta"
            return True, "Conexión RCON exitosa"
    except ConnectionRefusedError:
        return False, f"Puerto {port} cerrado (MC no corriendo o RCON inactivo)"
    except socket.timeout:
        return False, f"Timeout — servidor no respondió"
    except Exception as e:
        return False, str(e)


def _get_servers() -> list[dict]:
    """
    Devuelve lista de dicts con info de cada servidor encontrado.
    Busca carpetas que contengan server.properties dentro de SERVERS_DIR.
    """
    servers = []
    if not os.path.exists(SERVERS_DIR):
        return servers

    for entry in sorted(os.listdir(SERVERS_DIR)):
        full_path = os.path.join(SERVERS_DIR, entry)
        props_path = os.path.join(full_path, "server.properties")
        if os.path.isdir(full_path):
            rcon = _read_rcon_from_props(props_path)
            servers.append({
                "name":       entry,
                "path":       full_path,
                "props":      props_path,
                "has_props":  os.path.exists(props_path),
                "rcon_on":    rcon["enable-rcon"].lower() == "true",
                "rcon_port":  rcon["rcon.port"] or str(RCON_PORT),
                "rcon_pw":    bool(rcon["rcon.password"]),
            })
    return servers


# ─── Selector de servidor ─────────────────────────────────────────────────────

def _pick_server(servers: list[dict], prompt_text: str = "Selecciona un servidor") -> dict | None:
    """
    Muestra la tabla de servidores y pide al usuario elegir uno.
    Devuelve el dict del servidor elegido, o None si cancela.
    """
    if not servers:
        console.print("[red]No se encontraron servidores en[/red] " + SERVERS_DIR)
        return None

    table = Table(
        show_header=True,
        header_style="bold yellow",
        box=box.ROUNDED,
        expand=True,
        show_lines=True,
    )
    table.add_column("#", style="bold cyan", width=4, justify="center")
    table.add_column("Servidor", style="bold white")
    table.add_column("server.properties", justify="center")
    table.add_column("RCON activo", justify="center")
    table.add_column("Puerto RCON", justify="center")
    table.add_column("Contraseña", justify="center")

    for i, s in enumerate(servers, start=1):
        props_badge = "[green]✅[/green]" if s["has_props"] else "[red]❌[/red]"
        rcon_badge  = "[green]✅[/green]" if s["rcon_on"]  else "[red]❌[/red]"
        pw_badge    = "[green]✅[/green]" if s["rcon_pw"]  else "[yellow]⚠ vacía[/yellow]"
        port_str    = s["rcon_port"] if s["has_props"] else "—"
        table.add_row(str(i), s["name"], props_badge, rcon_badge, port_str, pw_badge)

    console.print(table)

    choices = [str(i) for i in range(1, len(servers) + 1)] + ["0"]
    choice = Prompt.ask(
        f"[bold yellow]{prompt_text}[/bold yellow] [dim](0 = cancelar)[/dim]",
        choices=choices
    )
    if choice == "0":
        return None
    return servers[int(choice) - 1]


def _pick_servers_multi(servers: list[dict]) -> list[dict]:
    """
    Muestra la tabla y permite elegir: un número, varios separados por coma, o 'todos'.
    """
    if not servers:
        console.print("[red]No se encontraron servidores en[/red] " + SERVERS_DIR)
        return []

    table = Table(
        show_header=True,
        header_style="bold yellow",
        box=box.ROUNDED,
        expand=True,
        show_lines=True,
    )
    table.add_column("#", style="bold cyan", width=4, justify="center")
    table.add_column("Servidor", style="bold white")
    table.add_column("server.properties", justify="center")
    table.add_column("RCON activo", justify="center")
    table.add_column("Puerto RCON", justify="center")
    table.add_column("Contraseña set", justify="center")

    for i, s in enumerate(servers, start=1):
        props_badge = "[green]✅[/green]" if s["has_props"] else "[red]❌[/red]"
        rcon_badge  = "[green]✅[/green]" if s["rcon_on"]  else "[red]❌[/red]"
        pw_badge    = "[green]✅[/green]" if s["rcon_pw"]  else "[yellow]⚠ vacía[/yellow]"
        port_str    = s["rcon_port"] if s["has_props"] else "—"
        table.add_row(str(i), s["name"], props_badge, rcon_badge, port_str, pw_badge)

    console.print(table)
    console.print("[dim]Escribe un número, varios separados por coma (1,3) o 'todos'[/dim]")

    raw = Prompt.ask("[bold yellow]Selecciona servidores[/bold yellow]", default="todos")

    if raw.strip().lower() == "todos":
        return servers

    selected = []
    for part in raw.split(","):
        part = part.strip()
        if part.isdigit():
            idx = int(part)
            if 1 <= idx <= len(servers):
                selected.append(servers[idx - 1])
    return selected


# ─── Acciones ────────────────────────────────────────────────────────────────

def _do_configure(servers_sel: list[dict], password: str):
    """Parchea los server.properties seleccionados y actualiza .env."""
    env = _read_env()
    env["RCON_HOST"]     = RCON_HOST
    env["RCON_PORT"]     = str(RCON_PORT)
    env["RCON_PASSWORD"] = password
    _write_env(env)
    console.print(f"\n[green]✅ .env actualizado[/green] → {ENV_FILE}")

    result_table = Table(box=box.SIMPLE, show_header=True, header_style="bold")
    result_table.add_column("Servidor")
    result_table.add_column("Resultado", justify="center")

    for s in servers_sel:
        ok = _patch_props(s["props"], password, RCON_PORT)
        result_table.add_row(
            s["name"],
            "[green]✅ Configurado[/green]" if ok else "[red]❌ Fallo (sin server.properties)[/red]"
        )
    console.print(result_table)

    console.print(Panel(
        f"[bold green]¡Configuración aplicada![/bold green]\n\n"
        f"[white]Host:[/white]     [cyan]{RCON_HOST}[/cyan]\n"
        f"[white]Puerto:[/white]   [cyan]{RCON_PORT}[/cyan]\n"
        f"[white]Password:[/white] [cyan]{'*' * len(password)}[/cyan] (en .env)\n\n"
        f"[yellow]Próximos pasos:[/yellow]\n"
        f"  1. Reinicia el/los servidores Minecraft (para leer los nuevos server.properties)\n"
        f"  2. Reinicia el backend Python (python main.py)\n"
        f"  3. Usa la opción [3] para probar la conexión",
        title="🔐 RCON Configurado",
        border_style="green"
    ))


# ─── Submenú principal ────────────────────────────────────────────────────────

@app.callback(invoke_without_command=True)
def main(ctx: typer.Context):
    if ctx.invoked_subcommand is None:
        run_interactive()


def run_interactive():
    while True:
        console.clear()
        console.print(Panel.fit(
            "[bold cyan]🔌 RCON Setup — App ↔ Minecraft[/bold cyan]\n"
            "[dim]RCON permite enviar comandos al servidor sin necesidad de stdin.[/dim]",
            border_style="cyan",
            box=box.ROUNDED
        ))

        env = _read_env()
        current_pw = env.get("RCON_PASSWORD", "")

        # Mini-status
        env_table = Table(show_header=False, box=box.SIMPLE)
        env_table.add_column("k", style="bold yellow")
        env_table.add_column("v", style="cyan")
        env_table.add_row("RCON_HOST",     env.get("RCON_HOST",     "no definido"))
        env_table.add_row("RCON_PORT",     env.get("RCON_PORT",     "no definido"))
        env_table.add_row("RCON_PASSWORD", "✅ configurada" if current_pw else "❌ vacía")
        console.print(env_table)
        console.print()

        console.print("[1] Configurar servidor(es) — contraseña automática")
        console.print("[2] Configurar servidor(es) — contraseña personalizada")
        console.print("[3] Probar conexión RCON en un servidor")
        console.print("[4] Ver estado detallado de todos los servidores")
        console.print("[0] Volver al menú principal")
        console.print()

        choice = Prompt.ask("Selecciona", choices=["1", "2", "3", "4", "0"], default="1")

        if choice == "0":
            break
        elif choice == "1":
            _flow_auto()
        elif choice == "2":
            _flow_custom()
        elif choice == "3":
            _flow_test()
        elif choice == "4":
            _flow_detail()

        Prompt.ask("\n[dim]Presiona Enter para continuar...[/dim]")


# ─── Flujos ───────────────────────────────────────────────────────────────────

def _flow_auto():
    console.clear()
    console.print(Panel.fit("[bold yellow]⚙ Configuración automática de RCON[/bold yellow]", border_style="yellow"))
    console.print("[dim]Se generará (o reutilizará) una contraseña segura y se aplicará a los servidores que elijas.[/dim]\n")

    servers = _get_servers()
    selected = _pick_servers_multi(servers)
    if not selected:
        console.print("[yellow]No se seleccionó ningún servidor.[/yellow]")
        return

    env = _read_env()
    existing_pw = env.get("RCON_PASSWORD", "")

    if existing_pw:
        reuse = Confirm.ask(f"\nYa existe una contraseña RCON en .env. ¿Reutilizarla?", default=True)
        password = existing_pw if reuse else _gen_password()
    else:
        password = _gen_password()
        console.print(f"\n[green]🔑 Contraseña generada automáticamente[/green] (24 caracteres aleatorios)")

    console.print()
    _do_configure(selected, password)


def _flow_custom():
    console.clear()
    console.print(Panel.fit("[bold yellow]⚙ Configuración con contraseña personalizada[/bold yellow]", border_style="yellow"))

    servers = _get_servers()
    selected = _pick_servers_multi(servers)
    if not selected:
        console.print("[yellow]No se seleccionó ningún servidor.[/yellow]")
        return

    password = Prompt.ask("\n[bold]Ingresa la contraseña RCON[/bold]")
    if len(password) < 8:
        console.print("[red]⚠ La contraseña debe tener al menos 8 caracteres.[/red]")
        return

    _do_configure(selected, password)


def _flow_test():
    console.clear()
    console.print(Panel.fit("[bold yellow]🔌 Probar conexión RCON[/bold yellow]", border_style="yellow"))
    console.print("[dim]Selecciona el servidor donde quieres probar la conexión.[/dim]\n")

    servers = _get_servers()
    selected = _pick_server(servers, "Selecciona el servidor a testear")
    if not selected:
        return

    env = _read_env()
    password = env.get("RCON_PASSWORD", "")
    if not password:
        console.print("[red]❌ No hay RCON_PASSWORD en .env. Configura primero con la opción [1].[/red]")
        return

    # El puerto lo leemos del server.properties seleccionado si está disponible
    rcon_data = _read_rcon_from_props(selected["props"])
    port = int(rcon_data["rcon.port"]) if rcon_data["rcon.port"].isdigit() else RCON_PORT

    console.print(f"\n[dim]Conectando a {RCON_HOST}:{port} para '{selected['name']}'...[/dim]")
    ok, msg = _rcon_test(RCON_HOST, port, password)

    if ok:
        console.print(Panel(
            f"[bold green]{msg}[/bold green]\n\n"
            f"El backend puede enviar comandos a [cyan]{selected['name']}[/cyan] correctamente.",
            border_style="green", title="✅ Test RCON — OK"
        ))
    else:
        console.print(Panel(
            f"[bold red]Fallo:[/bold red] {msg}\n\n"
            f"[yellow]Causas comunes:[/yellow]\n"
            f"  • El servidor [cyan]{selected['name']}[/cyan] no está corriendo\n"
            f"  • enable-rcon=true no está en server.properties\n"
            f"  • El servidor no fue reiniciado tras el parcheo\n"
            f"  • El puerto {port} está bloqueado internamente",
            border_style="red", title="❌ Test RCON — Fallido"
        ))


def _flow_detail():
    console.clear()
    console.print(Panel.fit("[bold yellow]📋 Estado RCON — Todos los servidores[/bold yellow]", border_style="yellow"))

    env = _read_env()
    env_table = Table(title="Variables en .env", box=box.ROUNDED, show_lines=True)
    env_table.add_column("Variable", style="bold yellow")
    env_table.add_column("Valor", style="cyan")
    env_table.add_row("RCON_HOST",     env.get("RCON_HOST",     "[dim]no definido[/dim]"))
    env_table.add_row("RCON_PORT",     env.get("RCON_PORT",     "[dim]no definido[/dim]"))
    env_table.add_row("RCON_PASSWORD", "✅ Configurada" if env.get("RCON_PASSWORD") else "❌ Vacía")
    console.print(env_table)
    console.print()

    servers = _get_servers()
    if not servers:
        console.print(f"[yellow]No hay servidores en {SERVERS_DIR}[/yellow]")
        return

    for s in servers:
        rcon = _read_rcon_from_props(s["props"])
        pt = Table(title=f"[bold]{s['name']}[/bold]", box=box.SIMPLE, show_lines=False)
        pt.add_column("Clave", style="yellow", width=20)
        pt.add_column("Valor en server.properties", style="green")
        pt.add_row("enable-rcon",  rcon["enable-rcon"]  or "[dim]no presente[/dim]")
        pt.add_row("rcon.port",    rcon["rcon.port"]    or "[dim]no presente[/dim]")
        pt.add_row("rcon.password","✅ Configurada" if rcon["rcon.password"] else "[dim]no presente[/dim]")
        console.print(pt)
