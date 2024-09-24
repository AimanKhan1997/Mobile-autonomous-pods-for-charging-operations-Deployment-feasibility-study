import xml.etree.ElementTree as ET
import xml.dom.minidom as minidom
import numpy as np

def prettify(elem):
    """Return a pretty-printed XML string for the Element."""
    rough_string = ET.tostring(elem, 'utf-8')
    reparsed = minidom.parseString(rough_string)
    return reparsed.toprettyxml(indent=" ")


def generate_electric_vehicle_routes(num_vehicles, route_id, route_edges, begin, end, min_capacity, max_capacity,
                                     mean_capacity, std_dev, repeat):
    root = ET.Element("routes", xmlns="http://sumo.dlr.de/xsd/routes_file.xsd")

    # Generate electric vehicle flows with fixed interval depart times and normally distributed battery capacities
    departure_interval = 10  # seconds
    for i in range(num_vehicles):
        depart_time = begin + i * departure_interval
        actual_capacity = max(min(np.random.normal(mean_capacity, std_dev), max_capacity), min_capacity)
        vehicle = ET.SubElement(root, "vehicle", id=f"f_0.{i}", type="ElectricVehicle", route=route_id,
                                depart=str(depart_time))
        param = ET.SubElement(vehicle, "param", key="device.battery.chargeLevel", value=str(actual_capacity))

    tree = ET.ElementTree(root)
    xml_string = prettify(root)
    with open("electric_vehicle_routes.rou.xml", "w") as f:
        f.write(xml_string)


# Example usage
generate_electric_vehicle_routes(
    num_vehicles=75,
    route_id="r_0",
    route_edges="E0 E1 E2 E3",
    begin=00.00,
    end=1999.00,
    min_capacity=200,
    max_capacity=640,
    mean_capacity=340,
    std_dev=130,
    repeat=10
)
