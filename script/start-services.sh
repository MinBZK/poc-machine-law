#!/bin/sh

# Multi-Instance Go App Runner Script
# Reads organization configs from YAML files and runs instances

set -e

# Application path (default to current directory)
APP_PATH="${1:-.}"

# Configuration directory (default to ./configs)
CONFIG_DIR="${2:-./configs}"

# Default starting port if not specified in config
DEFAULT_START_PORT=8081

# File to store process IDs for cleanup
PIDFILE="/tmp/go_instances_$$.pids"

# Function to cleanup processes on exit
cleanup() {
    echo "Shutting down application instances..."

    if [ -f "$PIDFILE" ]; then
        while IFS= read -r line; do
            if [ -n "$line" ]; then
                pid=$(echo "$line" | cut -d'|' -f1)
                name=$(echo "$line" | cut -d'|' -f2)

                if kill -0 "$pid" 2>/dev/null; then
                    echo "Stopping $name (PID: $pid)"
                    kill -TERM "$pid" 2>/dev/null || true
                fi
            fi
        done < "$PIDFILE"

        # Wait a moment for graceful shutdown
        sleep 2

        # Force kill if still running
        while IFS= read -r line; do
            if [ -n "$line" ]; then
                pid=$(echo "$line" | cut -d'|' -f1)
                name=$(echo "$line" | cut -d'|' -f2)

                if kill -0 "$pid" 2>/dev/null; then
                    echo "Force killing $name (PID: $pid)"
                    kill -KILL "$pid" 2>/dev/null || true
                fi
            fi
        done < "$PIDFILE"

        rm -f "$PIDFILE"
    fi

    echo "All instances stopped"
    exit 0
}

# Set up signal handlers
trap cleanup INT TERM

# Function to parse YAML-like config file
parse_config() {
    config_file="$1"
    org_id=$(basename "$config_file" .yaml)
    uuid=""
    name=""
    endpoint=""

    while IFS= read -r line; do
        # Skip empty lines and comments
        case "$line" in
            ""|\#*) continue ;;
        esac

        # Parse key-value pairs
        case "$line" in
            *:*)
                key=$(echo "$line" | cut -d':' -f1 | sed 's/[[:space:]]//g')
                value=$(echo "$line" | cut -d':' -f2- | sed 's/^[[:space:]]*//')

                case "$key" in
                    "uuid") uuid="$value" ;;
                    "name") name="$value" ;;
                    "endpoint") endpoint="$value" ;;
                esac
                ;;
        esac
    done < "$config_file"

    # Extract port from endpoint if available
    port=""
    case "$endpoint" in
        *:*[0-9])
            port=$(echo "$endpoint" | sed 's/.*:\([0-9]*\)$/\1/')
            ;;
    esac

    echo "$org_id|$uuid|$name|$endpoint|$port"
}

# Function to start a single instance
start_instance() {
    org_id="$1"
    uuid="$2"
    org_name="$3"
    endpoint="$4"
    port="$5"

    if [ ! -d "$APP_PATH" ]; then
        echo "Error: Directory $APP_PATH does not exist"
        return 1
    fi

    # Use provided port or fall back to auto-increment
    if [ -z "$port" ]; then
        # Count existing PIDs to determine next port
        instance_count=0
        if [ -f "$PIDFILE" ]; then
            instance_count=$(wc -l < "$PIDFILE")
        fi
        port=$((DEFAULT_START_PORT + instance_count))
        endpoint="http://localhost:$port"
    fi

    listen_addr="localhost:$port"
    instance_name="$org_name"

    echo "Starting instance '$instance_name' ($org_id) from $APP_PATH..."
    echo "  UUID: $uuid"
    echo "  Organization: $org_name"
    echo "  Listen Address: $listen_addr"
    echo "  Endpoint: $endpoint"

    # Start the instance in background with specific environment
    (
        cd "$APP_PATH"

        # Set environment variables for this instance
        APP_BACKEND_LISTEN_ADDRESS="$listen_addr"
        APP_INPUT_FILE=""
        APP_DEBUG="true"
        APP_ORGANIZATION="$org_name"
        APP_STANDALONE_MODE="true"
        APP_ORG_UUID="$uuid"
        APP_ORG_ID="$org_id"

        export APP_BACKEND_LISTEN_ADDRESS
        export APP_INPUT_FILE
        export APP_DEBUG
        export APP_ORGANIZATION
        export APP_STANDALONE_MODE
        export APP_ORG_UUID
        export APP_ORG_ID

        echo "[$instance_name] Starting go run . with environment:"
        echo "[$instance_name]   APP_BACKEND_LISTEN_ADDRESS=$APP_BACKEND_LISTEN_ADDRESS"
        echo "[$instance_name]   APP_INPUT_FILE=$APP_INPUT_FILE"
        echo "[$instance_name]   APP_DEBUG=$APP_DEBUG"
        echo "[$instance_name]   APP_ORGANIZATION=$APP_ORGANIZATION"
        echo "[$instance_name]   APP_STANDALONE_MODE=$APP_STANDALONE_MODE"
        echo "[$instance_name]   APP_ORG_UUID=$APP_ORG_UUID"
        echo "[$instance_name]   APP_ORG_ID=$APP_ORG_ID"

        go run . serve 2>&1 | sed "s/^/[$instance_name] /"
    ) &

    pid=$!
    echo "$pid|$instance_name" >> "$PIDFILE"
    echo "Started '$instance_name' with PID $pid on port $port"
}

# Function to create example config files if directory doesn't exist
create_example_configs() {
    config_dir="$1"

    echo "Creating example configuration directory: $config_dir"
    mkdir -p "$config_dir"

    # Create example config files
    cat > "$config_dir/org1.yaml" << 'EOF'
uuid: 9a144988-2b80-4e8a-adfb-43aa761a5ac4
name: CBS
endpoint: http://localhost:8081
EOF

    cat > "$config_dir/org2.yaml" << 'EOF'
uuid: 7b255a99-3c91-5f9b-bedc-54bb872b6bd5
name: NBC
endpoint: http://localhost:8082
EOF

    cat > "$config_dir/org3.yaml" << 'EOF'
uuid: 5c366baa-4da2-6g0c-cfed-65cc983c7ce6
name: ABC
endpoint: http://localhost:8083
EOF

    echo "Created example configuration files in $config_dir/"
    echo "You can modify these files or add more configurations."
}

# Main execution
echo "Starting Go application instances..."
echo "App Path: $APP_PATH"
echo "Config Directory: $CONFIG_DIR"

# Clean up any existing PID file
rm -f "$PIDFILE"

# Check if config directory exists
if [ ! -d "$CONFIG_DIR" ]; then
    echo "Configuration directory '$CONFIG_DIR' not found."
    printf "Would you like to create example configurations? (y/n): "
    read -r reply
    case "$reply" in
        [Yy]*)
            create_example_configs "$CONFIG_DIR"
            echo "Please review and modify the configurations, then run the script again."
            exit 0
            ;;
        *)
            echo "Exiting. Please create configuration files in '$CONFIG_DIR'"
            exit 1
            ;;
    esac
fi

echo "========================================"

# Check for YAML files
found_configs=false
for config_file in "$CONFIG_DIR"/*.yaml; do
    if [ -f "$config_file" ]; then
        found_configs=true
        break
    fi
done

if [ "$found_configs" = false ]; then
    echo "No YAML configuration files found in $CONFIG_DIR"
    echo "Expected files like: org1.yaml, org2.yaml, etc."
    exit 1
fi

# Parse and start instances
for config_file in "$CONFIG_DIR"/*.yaml; do
    if [ -f "$config_file" ]; then
        echo "Reading configuration: $(basename "$config_file")"

        # Parse the config file
        config_result=$(parse_config "$config_file")
        org_id=$(echo "$config_result" | cut -d'|' -f1)
        uuid=$(echo "$config_result" | cut -d'|' -f2)
        name=$(echo "$config_result" | cut -d'|' -f3)
        endpoint=$(echo "$config_result" | cut -d'|' -f4)
        port=$(echo "$config_result" | cut -d'|' -f5)

        if [ -z "$name" ]; then
            echo "Warning: No name found in $config_file, skipping..."
            continue
        fi

        start_instance "$org_id" "$uuid" "$name" "$endpoint" "$port"
        sleep 1  # Small delay between starts
    fi
done

echo "========================================"
echo "All instances started:"
if [ -f "$PIDFILE" ]; then
    while IFS= read -r line; do
        if [ -n "$line" ]; then
            pid=$(echo "$line" | cut -d'|' -f1)
            name=$(echo "$line" | cut -d'|' -f2)
            echo "  $name: PID $pid"
        fi
    done < "$PIDFILE"
fi
echo "Press Ctrl+C to stop all instances"

# Wait for all background processes
wait

echo "All instances have finished"
