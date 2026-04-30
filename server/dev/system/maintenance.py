import typer
import shutil
import os
import time
import glob
from dev.utils.core import print_header, print_success, print_info, print_warning, console
from rich.table import Table
import psutil

app = typer.Typer(help="System maintenance and utility tools")

@app.callback(invoke_without_command=True)
def main(ctx: typer.Context):
    if ctx.invoked_subcommand is None:
        from rich.prompt import Prompt
        from rich.panel import Panel
        
        while True:
            console.clear()
            console.print(Panel.fit("[bold green]🧹 Maintenance Manager[/bold green]", border_style="green"))
            console.print("[1] System Info (RAM, CPU, Disk)")
            console.print("[2] Clean Old Logs")
            console.print("[3] Check Disk Space")
            console.print("[0] Return to Main Menu")
            
            choice = Prompt.ask("Select an option", choices=["1", "2", "3", "0"], default="1")
            
            try:
                if choice == "1":
                    system_info()
                elif choice == "2":
                    days = Prompt.ask("Delete logs older than X days?", default="7")
                    clean_logs(int(days))
                elif choice == "3":
                    check_space()
                elif choice == "0":
                    break
            except Exception as e:
                console.print(f"[bold red]An error occurred: {e}[/bold red]")
                
            Prompt.ask("\n[dim]Press Enter to continue...[/dim]")

@app.command("info")
def system_info():
    """Show system resource usage (RAM, CPU, Disk)"""
    print_header("System Information")
    
    cpu_usage = psutil.cpu_percent(interval=1)
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage('.')
    
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Resource", style="dim")
    table.add_column("Usage", justify="right")
    table.add_column("Details")
    
    table.add_row("CPU", f"{cpu_usage}%", "Processing Power")
    table.add_row("RAM", f"{memory.percent}%", f"{memory.used // (1024*1024)}MB / {memory.total // (1024*1024)}MB")
    table.add_row("Disk (CWD)", f"{disk.percent}%", f"{disk.free // (1024*1024*1024)}GB Free")
    
    console.print(table)

@app.command("clean-logs")
def clean_logs(days: int = typer.Option(7, help="Delete logs older than X days")):
    """Delete old log files"""
    print_header(f"Cleaning logs older than {days} days")
    
    log_dir = "logs"
    if not os.path.exists(log_dir):
        print_warning("No logs directory found.")
        return

    now = time.time()
    deleted_count = 0
    
    for filename in os.listdir(log_dir):
        file_path = os.path.join(log_dir, filename)
        if os.path.isfile(file_path):
            file_age = now - os.path.getmtime(file_path)
            if file_age > (days * 86400):
                os.remove(file_path)
                deleted_count += 1
                console.print(f"[dim]Deleted {filename}[/dim]")
                
    if deleted_count > 0:
        print_success(f"Deleted {deleted_count} old log files.")
    else:
        print_info("No old logs found to delete.")

@app.command("check-space")
def check_space():
    """Quick check of available disk space"""
    total, used, free = shutil.disk_usage(".")
    print_header("Disk Storage")
    print_info(f"Total: {total // (2**30)} GB")
    print_info(f"Used: {used // (2**30)} GB")
    print_success(f"Free: {free // (2**30)} GB")
