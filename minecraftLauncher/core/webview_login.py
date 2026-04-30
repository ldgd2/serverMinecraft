import sys
import webview
import urllib.parse

def main():
    if len(sys.argv) < 3:
        print("Uso: python webview_login.py <login_url> <redirect_uri>")
        sys.exit(1)

    login_url = sys.argv[1]
    redirect_uri = sys.argv[2]

    # Crear ventana de WebView
    window = webview.create_window(
        "Iniciar Sesión con Microsoft", 
        login_url, 
        width=500, 
        height=660,
        resizable=False
    )

    def check_url():
        current_url = window.get_current_url()
        # Debug
        # sys.stderr.write(f"[WebView] URL: {current_url}\n")
        
        if redirect_uri in current_url and "code=" in current_url:
             parsed_url = urllib.parse.urlparse(current_url)
             params = urllib.parse.parse_qs(parsed_url.query)
             if 'code' in params:
                  code = params['code'][0]
                  # Imprimir el código a stdout para que el proceso padre lo lea
                  print(f"CODE:{code}")
                  window.destroy()
                  sys.exit(0)

    # El evento 'loaded' se dispara cada vez que la página cambia de URL 
    # (redirección)
    window.events.loaded += check_url

    # Iniciar
    webview.start()

if __name__ == "__main__":
    main()
