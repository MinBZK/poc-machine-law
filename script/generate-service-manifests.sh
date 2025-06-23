#!/bin/sh

set -e

# Default directories (can be overridden by parameters)
DEFAULT_SERVICES_DIR="./services"
DEFAULT_MANIFESTS_DIR="./deploy/manifests"

# Initialize variables
SERVICES_DIR=""
MANIFESTS_DIR=""

# Function to parse YAML values (simple key-value extraction)
parse_yaml() {
    file="$1"
    key="$2"
    value=""

    while IFS= read -r line; do
        # Skip empty lines and comments
        case "$line" in
            ""|\#*) continue ;;
        esac

        # Check if line contains a colon
        case "$line" in
            *:*)
                # Extract key and value
                line_key=$(echo "$line" | cut -d':' -f1 | sed 's/[[:space:]]*$//')
                line_value=$(echo "$line" | cut -d':' -f2- | sed 's/^[[:space:]]*//')

                # Remove quotes from value if present
                line_value=$(echo "$line_value" | sed 's/^["'"'"']//;s/["'"'"']$//')

                # Check if this is the key we're looking for
                if [ "$line_key" = "$key" ]; then
                    value="$line_value"
                    break
                fi
                ;;
        esac
    done < "$file"

    echo "$value"
}

# Function to generate base kustomization.yaml
generate_base_kustomization() {
    base_dir="$1"

    cat > "${base_dir}/kustomization.yaml" << EOF
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization
resources:
  - backend
  - inzicht-backend
EOF
}

# Function to generate backend kustomization.yaml
generate_backend_kustomization() {
    backend_dir="$1"
    service_name="$2"

    cat > "${backend_dir}/kustomization.yaml" << EOF
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization

namePrefix: backend-

resources:
  - deployment.yaml
  - service.yaml
  - ingress.yaml
  - otlp-collector.yaml

labels:
  - includeSelectors: true
    pairs:
      app: backend
      service: ${service_name}
EOF
}

# Function to generate deployment.yaml
generate_deployment() {
    backend_dir="$1"
    service_name="$2"
    service_id="$3"

    cat > "${backend_dir}/deployment.yaml" << EOF
apiVersion: apps/v1
kind: Deployment
metadata:
  name: dpl
spec:
  replicas: 1
  selector:
    matchLabels:
      app: backend
  template:
    metadata:
      labels:
        app: backend
      annotations:
        sidecar.opentelemetry.io/inject: "${service_id}-backend-otlp-collector"
    spec:
      containers:
        - name: ${service_id}-backend
          image: go-engine-backend-image
          env:
            - name: APP_DEBUG
              value: "true"
            - name: APP_ORGANIZATION
              value: "${service_name}"
            - name: APP_STANDALONE_MODE
              value: "true"
            - name: APP_RULE_SERVICE_IN_MEMORY
              value: "false"
            - name: APP_LDV_ENABLED
              value: "true"
            - name: APP_LDV_ENDPOINT
              value: "localhost:4317"
          ports:
            - name: http
              containerPort: 8080
          volumeMounts:
            - name: services-config
              mountPath: /build/services
              readOnly: true
      volumes:
        - name: services-config
          configMap:
            name: services-cm
EOF
}

# Function to generate service.yaml
generate_service() {
    backend_dir="$1"

    cat > "${backend_dir}/service.yaml" << 'EOF'
apiVersion: v1
kind: Service
metadata:
  name: svc
spec:
  selector:
    app: backend
  ports:
    - protocol: TCP
      port: 80
      targetPort: http
      name: http
EOF
}

# Function to generate ingress.yaml
generate_ingress() {
    backend_dir="$1"
    service_id="$2"

    cat > "${backend_dir}/ingress.yaml" << EOF
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: ing
  annotations:
    cert-manager.io/cluster-issuer: letsencrypt-prod
    nginx.ingress.kubernetes.io/enable-cors: "true"
    nginx.ingress.kubernetes.io/cors-allow-origin: "*"
    nginx.ingress.kubernetes.io/cors-allow-methods: "GET,HEAD,OPTIONS,TRACE,PUT,DELETE,POST,PATCH,CONNECT"
    nginx.ingress.kubernetes.io/cors-allow-headers: "DNT,Keep-Alive,User-Agent,X-Requested-With,If-Modified-Since,Cache-Control,Content-Type,Range,Authorization,X-Dpl-Core-User,X-Username"
spec:
  ingressClassName: nginx
  rules:
    - host: placeholder
      http:
        paths:
          - path: /
            pathType: Prefix
            backend:
              service:
                name: svc
                port:
                  name: http
  tls:
    - secretName: backend-tls
      hosts: []
EOF
}

# Function to generate inzicht-backend kustomization.yaml
generate_inzicht_backend_kustomization() {
    inzicht_backend_dir="$1"
    service_name="$2"

    cat > "${inzicht_backend_dir}/kustomization.yaml" << EOF
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization

namePrefix: inzicht-backend-

resources:
  - deployment.yaml
  - service.yaml
  - ingress.yaml

labels:
  - includeSelectors: true
    pairs:
      app: inzicht-backend
      service: ${service_name}
EOF
}

# Function to generate inzicht-backend deployment.yaml
generate_inzicht_backend_deployment() {
    inzicht_backend_dir="$1"
    service_name="$2"
    service_id="$3"

    cat > "${inzicht_backend_dir}/deployment.yaml" << EOF
apiVersion: apps/v1
kind: Deployment
metadata:
  name: dpl
spec:
  replicas: 1
  template:
    spec:
      containers:
        - name: inzicht-backend
          image: ldv-inzicht-backend-image
          env:
            - name: APP_ORGANIZATION
              value: "${service_name}"
            - name: APP_QUERY_ENDPOINT
              value: "clickhouse:9000"
            - name: APP_QUERY_DATABASE
              value: "${service_name}"
            - name: APP_QUERY_USER
              value: "clickhouse"
            - name: APP_QUERY_PASSWORD
              value: "clickhouse"
            - name: APP_RVA_CURRENT
              value: "static"
            - name: APP_RVA_STATIC_FILEPATH
              value: "/app/rva-config.yaml"
          ports:
            - name: http
              containerPort: 8080
          volumeMounts:
            - mountPath: /app/rva-config.yaml
              name: rva-config
              subPath: ${service_id}-rva-config.yaml
      volumes:
        - name: rva-config
          configMap:
            name: ${service_id}-rva-config-cm
EOF
}

# Function to generate inzicht-backend service.yaml
generate_inzicht_backend_service() {
    inzicht_backend_dir="$1"

    cat > "${inzicht_backend_dir}/service.yaml" << 'EOF'
apiVersion: v1
kind: Service
metadata:
  name: svc
spec:
  selector:
    app: inzicht-backend
  ports:
    - protocol: TCP
      port: 80
      targetPort: http
      name: http
EOF
}

# Function to generate inzicht-backend ingress.yaml
generate_inzicht_backend_ingress() {
    inzicht_backend_dir="$1"
    service_id="$2"

    cat > "${inzicht_backend_dir}/ingress.yaml" << EOF
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: ing
  annotations:
    cert-manager.io/cluster-issuer: letsencrypt-prod
    nginx.ingress.kubernetes.io/enable-cors: "true"
    nginx.ingress.kubernetes.io/cors-allow-origin: "*"
    nginx.ingress.kubernetes.io/cors-allow-methods: "GET,HEAD,OPTIONS,TRACE,PUT,DELETE,POST,PATCH,CONNECT"
    nginx.ingress.kubernetes.io/cors-allow-headers: "DNT,Keep-Alive,User-Agent,X-Requested-With,If-Modified-Since,Cache-Control,Content-Type,Range,Authorization,X-Dpl-Core-User,X-Username"
spec:
  ingressClassName: nginx
  rules:
    - host: placeholder
      http:
        paths:
          - path: /
            pathType: Prefix
            backend:
              service:
                name: svc
                port:
                  name: http
  tls:
    - secretName: backend-tls
      hosts: []
EOF
}

# Function to generate otlp-collector.yaml
generate_otlp_collector() {
    backend_dir="$1"
    service_name="$2"

    cat > "${backend_dir}/otlp-collector.yaml" << EOF
apiVersion: opentelemetry.io/v1alpha1
kind: OpenTelemetryCollector
metadata:
  name: otlp-collector
spec:
  image: otel/opentelemetry-collector-contrib:0.128.0
  mode: sidecar
  config: |
    receivers:
      otlp:
        protocols:
          grpc:

    exporters:
      clickhouse:
        endpoint: tcp://clickhouse:9000?dial_timeout=10s&compress=lz4
        username: clickhouse
        password: clickhouse
        database: ${service_name}
        traces_table_name: otel_traces
      debug:

    service:
      pipelines:
        traces:
          receivers: [otlp]
          processors: []
          exporters: [debug, clickhouse]
EOF
}

# Function to generate local overlay kustomization.yaml
generate_local_overlay_kustomization() {
    overlay_dir="$1"
    service_id="$2"
    service_uuid="$3"
    service_name="$4"

    cat > "${overlay_dir}/kustomization.yaml" << EOF
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization

namespace: lac
namePrefix: ${service_id}-

patches:
  - target:
      kind: Ingress
      name: backend-ing
    patch: |
      - op: replace
        path: /spec/rules/0/host
        value: ${service_id}-backend.127-0-0-1.nip.io
      - op: remove
        path: /spec/tls
  - target:
      kind: Ingress
      name: inzicht-backend-ing
    patch: |
      - op: replace
        path: /spec/rules/0/host
        value: ${service_id}-inzicht-backend.127-0-0-1.nip.io
      - op: remove
        path: /spec/tls

resources:
  - ../../base
EOF

}

# Function to setup service structure
setup_service_structure() {
    service_id="$1"
    service_uuid="$2"
    service_name="$3"
    service_endpoint="$4"

    echo "🏗️  Setting up structure for: $service_name"

    # Create service directories
    service_dir="${MANIFESTS_DIR}/${service_id}"
    base_dir="${service_dir}/base"
    backend_dir="${base_dir}/backend"
    inzicht_backend_dir="${base_dir}/inzicht-backend"
    overlays_dir="${service_dir}/overlays"
    local_overlay_dir="${overlays_dir}/local"

    mkdir -p "$backend_dir"
    mkdir -p "$inzicht_backend_dir"
    mkdir -p "$local_overlay_dir"

    # Generate base files
    generate_base_kustomization "$base_dir"
    generate_backend_kustomization "$backend_dir" "$service_name"
    generate_deployment "$backend_dir" "$service_name" "$service_id"
    generate_service "$backend_dir"
    generate_ingress "$backend_dir" "$service_id"
    generate_otlp_collector "$backend_dir" "$service_name"

    # Generate inzicht-backend files
    generate_inzicht_backend_kustomization "$inzicht_backend_dir" "$service_name"
    generate_inzicht_backend_deployment "$inzicht_backend_dir" "$service_name" "$service_id"
    generate_inzicht_backend_service "$inzicht_backend_dir"
    generate_inzicht_backend_ingress "$inzicht_backend_dir" "$service_id"

    # Generate local overlay
    generate_local_overlay_kustomization "$local_overlay_dir" "$service_id" "$service_uuid" "$service_name"

    echo "✅ Structure created for: $service_name (ID: $service_id)"
}

# Function to update rijksoverheid frontend-config.json with all inzicht-backend URLs
update_rijksoverheid_frontend_config() {
    manifests_dir="$1"
    services_dir="$2"
    shift 2
    service_ids="$@"

    frontend_config_file="${manifests_dir}/rijksoverheid/overlays/local/frontend-config.json"

    echo "📝 Updating rijksoverheid frontend-config.json with inzicht-backend URLs"

    # Start building the JSON file
    cat > "$frontend_config_file" << 'EOF'
{
  "backendAddresses": [
EOF

    # Add each service's inzicht-backend URL
    for service_id in $service_ids; do
      echo "    \"http://${service_id}-inzicht-backend.127-0-0-1.nip.io:8080\"" >> "$frontend_config_file"
    done

    # Go back and add commas to all lines except the last one
    sed -i '3,$s/$/,/' "$frontend_config_file"
    sed -i '$s/,$//' "$frontend_config_file"

    # Close the JSON structure
    cat >> "$frontend_config_file" << 'EOF'

  ]
}
EOF

    echo "   📝 Updated rijksoverheid frontend-config.json with $(echo "$service_ids" | wc -w) inzicht-backend URLs"
}

# Function to generate org-specific rva-config files
generate_rva_config_files() {
    manifests_dir="$1"
    services_dir="$2"
    shift 2
    service_ids="$@"

    local_overlay_dir="${manifests_dir}/overlays/local"
    rva_configs_dir="${local_overlay_dir}/rva-configs"

    echo "📝 Generating org-specific rva-config files"

    # Create rva-configs directory
    mkdir -p "$rva_configs_dir"

    # Process each service to create its rva-config
    for service_file in "$services_dir"/*.yaml "$services_dir"/*.yml; do
        [ ! -f "$service_file" ] && continue

        service_name=$(parse_yaml "$service_file" "name")
        if [ -n "$service_name" ]; then
            service_name_k8s=$(echo "$service_name" | tr '[:upper:]' '[:lower:]' | tr '_' '-')
            rva_config_file="${rva_configs_dir}/${service_name_k8s}-rva-config.yaml"

            # Only create if it doesn't exist to avoid overwriting existing configs
            if [ ! -f "$rva_config_file" ]; then
                # Create a basic rva-config template for each organization
                cat > "$rva_config_file" << EOF
activities:
  example-activity-id:
    name: Example Activity for ${service_name}
    personaldatacategories:
      - Burgerservicenummer
EOF
                echo "   📝 Created rva-config for $service_name: rva-configs/${service_name_k8s}-rva-config.yaml"
            else
                echo "   ✅ Using existing rva-config for $service_name: rva-configs/${service_name_k8s}-rva-config.yaml"
            fi
        fi
    done
}

# Function to generate main kustomization.yaml
generate_main_kustomization() {
    manifests_dir="$1"
    services_dir="$2"
    shift 2
    service_ids="$@"

    echo "📝 Generating main kustomization.yaml"

    # Create overlays/local directory structure
    local_overlay_dir="${manifests_dir}/overlays/local"
    mkdir -p "$local_overlay_dir"

    cat > "${local_overlay_dir}/kustomization.yaml" << EOF
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization
namespace: lac

resources:
EOF

    # Add each service overlay to resources (adjust path for new location)
    for service_id in $service_ids; do
        echo "  - ../../${service_id}/overlays/local" >> "${local_overlay_dir}/kustomization.yaml"
    done

    # Copy services files to local overlay directory for configmap
    services_local_dir="${local_overlay_dir}/services"
    mkdir -p "$services_local_dir"

    # Copy and modify service files with correct endpoints
    for service_file in "$services_dir"/*.yaml "$services_dir"/*.yml; do
        [ ! -f "$service_file" ] && continue

        service_filename=$(basename "$service_file")
        # Use name field from YAML
        service_name=$(parse_yaml "$service_file" "name")

        # Convert service_name to lowercase and replace underscores with hyphens for k8s naming
        if [ -n "$service_name" ]; then
            service_name_k8s=$(echo "$service_name" | tr '[:upper:]' '[:lower:]' | tr '_' '-')
        fi

        # Copy file and replace endpoint with correct internal service URL
        if [ -n "$service_name_k8s" ]; then
            sed "s|^endpoint:.*|endpoint: http://${service_name_k8s}-backend-svc.lac.svc.cluster.local|g" "$service_file" > "$services_local_dir/$service_filename"
            echo "   📝 Updated endpoint for $service_name to http://${service_name_k8s}-backend-svc.lac.svc.cluster.local"
        else
            echo "   ⚠️  No service_name found for $service_filename, copying without modification"
            cp "$service_file" "$services_local_dir/"
        fi
    done

    # Add configmap generators for services and rva-configs
    cat >> "${local_overlay_dir}/kustomization.yaml" << EOF

configMapGenerator:
  - name: services-cm
    files:
EOF

    # Add all service files to the services configmap
    for service_file in "$services_local_dir"/*.yaml "$services_local_dir"/*.yml; do
        [ ! -f "$service_file" ] && continue
        service_filename=$(basename "$service_file")
        echo "      - services/${service_filename}" >> "${local_overlay_dir}/kustomization.yaml"
    done

    # Add individual configmaps for each org's rva-config
    for service_id in $service_ids; do
        cat >> "${local_overlay_dir}/kustomization.yaml" << EOF
  - name: ${service_id}-rva-config-cm
    files:
      - rva-configs/${service_id}-rva-config.yaml
EOF
    done

    cat >> "${local_overlay_dir}/kustomization.yaml" << EOF
images:
  - name: ldv-inzicht-backend-image
    newName: digilabpublic.azurecr.io/digilab.overheid.nl/ecosystem/logboek-dataverwerkingen/logboek-dataverwerkingen/backend
    newTag: 3729bd7f-main-106
EOF

}

# Function to clean manifests directory (with skiplist protection)
clean_manifests_directory() {
    manifests_dir="$1"

    # Skiplist of directories/files that should not be deleted
    skiplist="rijksoverheid toeslagen overlays"

    echo "🧹 Cleaning manifests directory: $manifests_dir"

    if [ -d "$manifests_dir" ]; then
        # Remove all directories except those in skiplist
        for item in "$manifests_dir"/*; do
            [ ! -e "$item" ] && continue  # Skip if no files match

            item_name=$(basename "$item")
            skip_item=false

            # Check if item is in skiplist
            for skiplisted in $skiplist; do
                if [ "$item_name" = "$skiplisted" ]; then
                    echo "   ⚠️  Skipping listed item: $item_name"
                    skip_item=true
                    break
                fi
            done

            # Remove item if not skiplisted
            if [ "$skip_item" = false ]; then
                echo "   🗑️  Removing: $item_name"
                rm -rf "$item"
            fi
        done
    else
        echo "   📁 Directory doesn't exist yet, will be created"
    fi
    echo ""
}

# Main function
main() {
    echo "🚀 Generating individual Kustomize structures for each service..."
    echo "📁 Services directory: $SERVICES_DIR"
    echo "📁 Manifests directory: $MANIFESTS_DIR"
    echo ""

    # Clean manifests directory before generating new files
    clean_manifests_directory "$MANIFESTS_DIR"

    # Check if services directory exists
    if [ ! -d "$SERVICES_DIR" ]; then
        echo "❌ Error: Directory '$SERVICES_DIR' does not exist"
        echo "💡 Please create the '$SERVICES_DIR' directory and add your service YAML files"
        exit 1
    fi

    # Create manifests directory if it doesn't exist
    mkdir -p "$MANIFESTS_DIR"

    # Counter for generated services
    count=0

    # Track service IDs for main kustomization
    service_ids=""

    # Process each YAML file in the services directory
    for service_file in "$SERVICES_DIR"/*.yaml "$SERVICES_DIR"/*.yml; do
        # Skip if no files match the pattern
        [ ! -f "$service_file" ] && continue

        echo "📄 Processing: $(basename "$service_file")"

        # Parse service details from YAML
        service_uuid=$(parse_yaml "$service_file" "uuid")
        service_name=$(parse_yaml "$service_file" "name")
        service_endpoint=$(parse_yaml "$service_file" "endpoint")

        # Convert service_name to lowercase and replace underscores with hyphens for folder names
        service_name_k8s=$(echo "$service_name" | tr '[:upper:]' '[:lower:]' | tr '_' '-')

        # Validate required fields
        if [ -z "$service_name" ] || [ -z "$service_uuid" ] || [ -z "$service_endpoint" ]; then
            echo "⚠️  Warning: Skipping $(basename "$service_file") - missing required fields"
            echo "   Found: name='$service_name', uuid='$service_uuid', endpoint='$service_endpoint'"
            continue
        fi

        # Setup service structure
        setup_service_structure "$service_name_k8s" "$service_uuid" "$service_name" "$service_endpoint"

        # Add service_name_k8s to list for main kustomization
        if [ -z "$service_ids" ]; then
            service_ids="$service_name_k8s"
        else
            service_ids="$service_ids $service_name_k8s"
        fi

        count=$((count + 1))
    done

    if [ $count -eq 0 ]; then
        echo "⚠️  No valid service files found in '$SERVICES_DIR'"
        echo "💡 Service files should have .yaml or .yml extension and contain: id, uuid, name, endpoint"
    else
        # Generate org-specific rva-config files, update rijksoverheid frontend-config.json, and main kustomization.yaml
        if [ -n "$service_ids" ]; then
            update_rijksoverheid_frontend_config "$MANIFESTS_DIR" "$SERVICES_DIR" "$service_ids"
            generate_rva_config_files "$MANIFESTS_DIR" "$SERVICES_DIR" "$service_ids"
            generate_main_kustomization "$MANIFESTS_DIR" "$SERVICES_DIR" "$service_ids"
        fi

        echo ""
        echo "🎉 Successfully generated $count service structures!"
        echo ""
        echo "🚀 To deploy all services locally, run:"
        echo "   kubectl apply -k $MANIFESTS_DIR/overlays/local"
        echo ""
        echo "🔧 To deploy individual services, run:"
        for service_file in "$SERVICES_DIR"/*.yaml "$SERVICES_DIR"/*.yml; do
            [ ! -f "$service_file" ] && continue
            service_name=$(parse_yaml "$service_file" "name")
            if [ -n "$service_name" ]; then
                service_name_k8s=$(echo "$service_name" | tr '[:upper:]' '[:lower:]' | tr '_' '-')
                echo "   kubectl apply -k $MANIFESTS_DIR/$service_name_k8s/overlays/local"
                break
            fi
        done
        echo ""
        echo "🌐 Services will be available at:"
        for service_file in "$SERVICES_DIR"/*.yaml "$SERVICES_DIR"/*.yml; do
            [ ! -f "$service_file" ] && continue
            service_name=$(parse_yaml "$service_file" "name")
            if [ -n "$service_name" ]; then
                service_name_k8s=$(echo "$service_name" | tr '[:upper:]' '[:lower:]' | tr '_' '-')
                echo "   Backend: http://$service_name_k8s-backend.127-0-0-1.nip.io:8080"
                echo "   Inzicht Backend: http://$service_name_k8s-inzicht-backend.127-0-0-1.nip.io:8080"
            fi
        done
    fi
}

# Help function
show_help() {
    cat << EOF
Usage: $0 [OPTIONS] [SERVICES_DIR] [MANIFESTS_DIR]

Generate individual Kustomize structures for each service based on YAML configuration files.

ARGUMENTS:
    SERVICES_DIR   Directory containing service YAML files (default: $DEFAULT_SERVICES_DIR)
    MANIFESTS_DIR  Directory where manifests will be generated (default: $DEFAULT_MANIFESTS_DIR)

OPTIONS:
    -h, --help     Show this help message

EXAMPLES:
    $0                                    # Use default directories
    $0 my-services                        # Use custom services directory, default manifests
    $0 my-services generated              # Use custom directories
    $0 -h                                 # Show help

DIRECTORY STRUCTURE:
    This script expects:

    <SERVICES_DIR>/                       # Service YAML files
    ├── cbs.yaml
    ├── dji.yaml
    └── ...

    And will generate:

    <MANIFESTS_DIR>/                      # Generated manifests per service
    ├── cbs/
    │   ├── base/
    │   │   ├── kustomization.yaml
    │   │   ├── backend/
    │   │   │   ├── kustomization.yaml
    │   │   │   ├── deployment.yaml
    │   │   │   ├── service.yaml
    │   │   │   └── ingress.yaml
    │   │   └── inzicht-backend/
    │   │       ├── kustomization.yaml
    │   │       ├── deployment.yaml
    │   │       ├── service.yaml
    │   │       └── ingress.yaml
    │   └── overlays/
    │       └── local/
    │           └── kustomization.yaml
    └── dji/
        ├── base/
        │   ├── kustomization.yaml
        │   ├── backend/
        │   │   ├── kustomization.yaml
        │   │   ├── deployment.yaml
        │   │   ├── service.yaml
        │   │   └── ingress.yaml
        │   └── inzicht-backend/
        │       ├── kustomization.yaml
        │       ├── deployment.yaml
        │       ├── service.yaml
        │       └── ingress.yaml
        └── overlays/
            └── local/
                └── kustomization.yaml

SERVICE YAML FORMAT:
    Each service file should contain:

    id: cbs
    uuid: 34e50b87-5e86-4dcf-b65a-ddfc44228f6e
    name: CBS
    endpoint: http://localhost:8081

FEATURES:
    - Creates separate namespace per service
    - Service-specific hostnames (e.g., cbs-backend.127-0-0-1.nip.io:8080)
    - Configures APP_ORGANIZATION environment variable
    - Removes TLS for local development in local overlay
    - Adds service labels to all resources

EOF
}

# Parse command line arguments
case "${1:-}" in
    -h|--help)
        show_help
        exit 0
        ;;
    *)
        # Set directories based on parameters
        SERVICES_DIR="${1:-$DEFAULT_SERVICES_DIR}"
        MANIFESTS_DIR="${2:-$DEFAULT_MANIFESTS_DIR}"

        # If first argument looks like a directory, proceed with main
        # Otherwise show error
        if [ -n "$1" ] && [ "$1" != "-h" ] && [ "$1" != "--help" ]; then
            main
        elif [ -z "$1" ]; then
            # No arguments, use defaults
            main
        else
            echo "❌ Error: Unknown option '$1'"
            echo "💡 Use '$0 --help' for usage information"
            exit 1
        fi
        ;;
esac
