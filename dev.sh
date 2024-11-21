#!/bin/bash
# ----------------------------------------------------------------
# Build docker dev stage and add local code for live development
# ----------------------------------------------------------------

# Default value for headless
headless=false

# Function to print usage
usage() {
    echo "Usage: dev.sh [--path | -p ] [--headless] [--help | -h]"
    echo ""
    echo "Options:"
    echo "  --path, -p ROSBAGS_DIR_PATH"
    echo "                 Specify path to store recorded rosbags"
    echo "  --headless     Run the Docker image without X11 forwarding"
    echo "  --help, -h     Display this help message and exit."
    echo ""
}

# Parse command-line options
while [[ "$#" -gt 0 ]]; do
    case $1 in
            # Option to specify path
        -p|--path)
            if [ -n "$2" ]; then
                ROSBAGS_DIR="$2"
                shift
            else
                echo "Error: Argument for $1 is missing."
                usage
            fi
            ;;
        --headless) headless=true ;;
        -h|--help)
            usage
            ;;
        *)
            echo "Unknown option: $1"
            usage
            ;;
    esac
    shift
done


MOUNT_X=""
if [ "$headless" = "false" ]; then
    MOUNT_X="-e DISPLAY=$DISPLAY -v /tmp/.X11-unix/:/tmp/.X11-unix"
    xhost + >/dev/null
fi

# Build
docker build \
    -t liosam:latest-dev \
    -f Dockerfile --target dev .

# Get the absolute path of the script
SCRIPT_DIR=$(dirname "$(readlink -f "${BASH_SOURCE[0]}")")

# Run docker image with local code volumes for development
docker run -it --rm --net host --privileged \
    --gpus all \
    -e NVIDIA_DRIVER_CAPABILITIES=all \
    ${MOUNT_X} \
    -e XAUTHORITY="${XAUTHORITY}" \
    -e XDG_RUNTIME_DIR="$XDG_RUNTIME_DIR" \
    -v /dev:/dev \
    -v /tmp:/tmp \
    -v $SCRIPT_DIR/cyclone_dds.xml:/opt/ros_ws/src/lio_sam/cyclone_dds.xml \
    -v $SCRIPT_DIR/config:/opt/ros_ws/src/lio_sam/config \
    -v $SCRIPT_DIR/launch:/opt/ros_ws/src/lio_sam/launch \
    -v /etc/localtime:/etc/localtime:ro \
    liosam:latest-dev
