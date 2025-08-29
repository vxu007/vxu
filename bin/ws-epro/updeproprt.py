print("\033[1;31m⚙︎ Voltssh-X} 'ULTIMATE' by @voltsshx ⚙︎")
print("\033[1;33m  ⌯ WebSocket(ePRO) Config Updater\033[1;33m")
print("    ------++------++------++------")
print(" ")

def update_config(config_file, openssh_port, wsopenssh_port):
    try:
        # Clear existing content by opening the file in "w" mode
        with open(config_file, "w") as f:
            # Write the specified content to the file
            f.write("# verbose level 0=info, 1=verbose, 2=very verbose\n")
            f.write("verbose: 0\n")
            f.write("listen:\n")
            f.write("##localHost\n")
            f.write("- target_host: 127.0.0.1\n")
            f.write("##openSSH\n")
            f.write(f"  target_port: {openssh_port}\n")
            f.write("##webSocketPro:\n")
            f.write(f"  listen_port: {wsopenssh_port}\n")

        print("\033[1;32m ")
        print("  * * * * * * ** * * * * * ")
        print("Config updated successfully!")
        print("  * * * * * * ** * * * * * ")
        print("\033[0m")
    except Exception as e:
        print("\033[1;31m ")
        print(f"Error: Failed to update config: {e}")
        print(" ")
        print("\033[0m")

if __name__ == "__main__":
    config_file = "/etc/vxu/ws-epro/config.yml"
    openssh_port = input("Enter openSSH port(eg: 22): ")
    wsopenssh_port = input("Enter webSocketPro port(eg: 80): ")
    update_config(config_file, openssh_port, wsopenssh_port)
