"""Convert collected native coverage data to Cobertura XML."""

from xml.etree.ElementTree import Element, ElementTree, SubElement, indent


def to_cobertura_xml(coverage_data, output_file):
    """Convert coverage_data to Cobertura XML and write output_file."""
    root_node = Element("coverage")

    sources_node = SubElement(root_node, "sources")
    source_node = SubElement(sources_node, "source")
    source_node.text = "."

    packages_node = SubElement(root_node, "packages")
    for package_name, classes in coverage_data.items():
        package_node = SubElement(
            packages_node,
            "package",
            attrib={"name": package_name, "line-rate": "1.0"},
        )

        classes_node = SubElement(package_node, "classes")
        for class_name, methods in classes.items():
            class_node = SubElement(classes_node, "class", name=class_name)
            methods_node = SubElement(class_node, "methods")
            for method_name, is_covered in methods.items():
                if not is_covered:
                    continue
                SubElement(
                    methods_node,
                    "method",
                    attrib={"name": method_name, "line-rate": "1.0"},
                )

    xml_tree = ElementTree(root_node)
    indent(xml_tree, space="\t", level=0)
    xml_tree.write(output_file, encoding="utf-8", xml_declaration=True)
