import xml.etree.ElementTree as ET
import matplotlib.pyplot as plt


# Function to parse the XML file and extract the relevant data
def parse_xml(file_path):
    tree = ET.parse(file_path)
    root = tree.getroot()

    edge_data = {}

    for interval in root.findall('interval'):
        for edge in interval.findall('edge'):
            edge_id = edge.get('id')
            if edge_id not in edge_data:
                edge_data[edge_id] = {
                    'density': [],
                    'speed': [],
                    'traveltime': []
                }

            edge_data[edge_id]['density'].append(float(edge.get('density')))
            edge_data[edge_id]['speed'].append(float(edge.get('speed')))
            edge_data[edge_id]['traveltime'].append(float(edge.get('traveltime')))

    return edge_data


# Function to plot the data using boxplots
def plot_boxplots(edge_data):
    edges = list(edge_data.keys())
    densities = [metrics['density'] for metrics in edge_data.values()]
    speeds = [metrics['speed'] for metrics in edge_data.values()]
    time_losses = [metrics['traveltime'] for metrics in edge_data.values()]

    plt.figure(figsize=(14, 8))

    plt.subplot(3, 1, 1)
    plt.boxplot(densities, labels=edges)
    plt.xlabel('Edge ID')
    plt.ylabel('Density')
    plt.title('Density Per Edge')
    plt.grid(True)

    plt.subplot(3, 1, 2)
    plt.boxplot(speeds, labels=edges)
    plt.xlabel('Edge ID')
    plt.ylabel('Speed (m/s)')
    plt.title('Speed Per Edge')
    plt.grid(True)

    plt.subplot(3, 1, 3)
    plt.boxplot(time_losses, labels=edges)
    plt.xlabel('Edge ID')
    plt.ylabel('Travel Time (s)')
    plt.title('Travel Time Per Edge')
    plt.grid(True)

    plt.tight_layout()
    plt.show()


# Function to print the average values of density, speed, and time loss per edge
def print_edge_data(edge_data):
    for edge_id, metrics in edge_data.items():
        avg_density = sum(metrics['density']) / len(metrics['density'])
        avg_speed = sum(metrics['speed']) / len(metrics['speed'])
        avg_time_loss = sum(metrics['traveltime']) / len(metrics['traveltime'])

        print(f"Edge ID: {edge_id}")
        print(f"  Average Density: {avg_density:.2f}")
        print(f"  Average Speed: {avg_speed:.2f}")
        print(f"  Average Travel Time: {avg_time_loss:.2f}")
        print()

# Main function to execute the workflow
def main(file_path):
    edge_data = parse_xml(file_path)
    plot_boxplots(edge_data)
    print_edge_data(edge_data)  # Print the edge data
# Execute the main function with the path to the XML file
file_path = 'data_only_EV.xml'
main(file_path)