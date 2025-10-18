"""
Draw.io export functionality for AAA diagrams.
Supports exporting Mermaid diagrams and Infrastructure specifications to Draw.io format.
"""

import json
from typing import Dict, Any, List
from urllib.parse import quote
import uuid
from datetime import datetime

from app.utils.logger import app_logger


class DrawIOExporter:
    """Export diagrams to Draw.io compatible formats."""

    def __init__(self):
        self.app_logger = app_logger

    def export_mermaid_diagram(
        self, mermaid_code: str, diagram_title: str, output_path: str
    ) -> str:
        """
        Export Mermaid diagram to Draw.io format.
        Draw.io has native Mermaid support, so we embed the Mermaid code.
        """
        try:
            # Create Draw.io XML structure with embedded Mermaid
            drawio_xml = self._create_mermaid_drawio_xml(mermaid_code, diagram_title)

            # Write to file
            output_file = f"{output_path}.drawio"
            with open(output_file, "w", encoding="utf-8") as f:
                f.write(drawio_xml)

            self.app_logger.info(f"Exported Mermaid diagram to Draw.io: {output_file}")
            return output_file

        except Exception as e:
            self.app_logger.error(f"Failed to export Mermaid to Draw.io: {e}")
            raise

    def export_infrastructure_diagram(
        self, infrastructure_spec: Dict[str, Any], diagram_title: str, output_path: str
    ) -> str:
        """
        Export Infrastructure diagram specification to Draw.io format.
        Converts the JSON spec to Draw.io XML with cloud provider shapes.
        """
        try:
            # Create Draw.io XML from infrastructure specification
            drawio_xml = self._create_infrastructure_drawio_xml(
                infrastructure_spec, diagram_title
            )

            # Write to file
            output_file = f"{output_path}.drawio"
            with open(output_file, "w", encoding="utf-8") as f:
                f.write(drawio_xml)

            self.app_logger.info(
                f"Exported Infrastructure diagram to Draw.io: {output_file}"
            )
            return output_file

        except Exception as e:
            self.app_logger.error(f"Failed to export Infrastructure to Draw.io: {e}")
            raise

    def _create_mermaid_drawio_xml(self, mermaid_code: str, title: str) -> str:
        """Create Draw.io XML with embedded Mermaid diagram."""

        # Escape Mermaid code for XML
        escaped_mermaid = self._escape_xml(mermaid_code)

        # Create Draw.io XML structure
        xml_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<mxfile host="AAA-Export" modified="{datetime.now().isoformat()}" agent="AAA-System" version="1.0" etag="{uuid.uuid4()}" type="device">
  <diagram id="{uuid.uuid4()}" name="{self._escape_xml(title)}">
    <mxGraphModel dx="1422" dy="794" grid="1" gridSize="10" guides="1" tooltips="1" connect="1" arrows="1" fold="1" page="1" pageScale="1" pageWidth="827" pageHeight="1169" math="0" shadow="0">
      <root>
        <mxCell id="0"/>
        <mxCell id="1" parent="0"/>
        <mxCell id="mermaid-cell" value="{escaped_mermaid}" style="shape=mxgraph.mermaid.abstract.mermaidChart;mermaidString={quote(mermaid_code)};fillColor=#ffffff;strokeColor=#000000;" vertex="1" parent="1">
          <mxGeometry x="40" y="40" width="740" height="500" as="geometry"/>
        </mxCell>
        <mxCell id="title-cell" value="{self._escape_xml(title)}" style="text;html=1;strokeColor=none;fillColor=none;align=center;verticalAlign=middle;whiteSpace=wrap;rounded=0;fontSize=16;fontStyle=1;" vertex="1" parent="1">
          <mxGeometry x="40" y="10" width="740" height="30" as="geometry"/>
        </mxCell>
        <mxCell id="export-info" value="Exported from AAA System - {datetime.now().strftime('%Y-%m-%d %H:%M')}" style="text;html=1;strokeColor=none;fillColor=none;align=right;verticalAlign=middle;whiteSpace=wrap;rounded=0;fontSize=10;fontColor=#666666;" vertex="1" parent="1">
          <mxGeometry x="580" y="550" width="200" height="20" as="geometry"/>
        </mxCell>
      </root>
    </mxGraphModel>
  </diagram>
</mxfile>"""

        return xml_content

    def _create_infrastructure_drawio_xml(
        self, spec: Dict[str, Any], title: str
    ) -> str:
        """Create Draw.io XML from infrastructure specification with cloud shapes."""

        # Start building the XML
        diagram_id = str(uuid.uuid4())

        xml_parts = [
            '<?xml version="1.0" encoding="UTF-8"?>',
            f'<mxfile host="AAA-Export" modified="{datetime.now().isoformat()}" agent="AAA-System" version="1.0" etag="{uuid.uuid4()}" type="device">',
            f'  <diagram id="{diagram_id}" name="{self._escape_xml(title)}">',
            '    <mxGraphModel dx="1422" dy="794" grid="1" gridSize="10" guides="1" tooltips="1" connect="1" arrows="1" fold="1" page="1" pageScale="1" pageWidth="1169" pageHeight="827" math="0" shadow="0">',
            "      <root>",
            '        <mxCell id="0"/>',
            '        <mxCell id="1" parent="0"/>',
        ]

        # Add title
        xml_parts.append(
            f"""        <mxCell id="title" value="{self._escape_xml(title)}" style="text;html=1;strokeColor=none;fillColor=none;align=center;verticalAlign=middle;whiteSpace=wrap;rounded=0;fontSize=18;fontStyle=1;" vertex="1" parent="1">
          <mxGeometry x="40" y="20" width="1089" height="30" as="geometry"/>
        </mxCell>"""
        )

        # Track positions and cells
        cell_counter = 1
        positions = {}
        y_offset = 80
        cluster_height = 200

        # Process clusters
        clusters = spec.get("clusters", [])
        for i, cluster in enumerate(clusters):
            cluster_id = f"cluster_{cell_counter}"
            cell_counter += 1

            cluster_name = cluster.get("name", f"Cluster {i+1}")
            provider = cluster.get("provider", "aws")

            # Cluster container
            cluster_x = 50 + (i % 3) * 350
            cluster_y = y_offset + (i // 3) * (cluster_height + 50)

            xml_parts.append(
                f"""        <mxCell id="{cluster_id}" value="{self._escape_xml(cluster_name)}" style="swimlane;whiteSpace=wrap;html=1;fillColor=#e1d5e7;strokeColor=#9673a6;fontStyle=1;" vertex="1" parent="1">
          <mxGeometry x="{cluster_x}" y="{cluster_y}" width="300" height="{cluster_height}" as="geometry"/>
        </mxCell>"""
            )

            # Process nodes in cluster
            nodes = cluster.get("nodes", [])
            for j, node in enumerate(nodes):
                node_id = node.get("id", f"node_{cell_counter}")
                cell_counter += 1

                node_label = node.get("label", node_id)
                node_type = node.get("type", "server")

                # Position nodes within cluster
                node_x = 20 + (j % 2) * 140
                node_y = 40 + (j // 2) * 80

                # Get shape style based on provider and type
                shape_style = self._get_drawio_shape_style(provider, node_type)

                xml_parts.append(
                    f"""        <mxCell id="{node_id}" value="{self._escape_xml(node_label)}" style="{shape_style}" vertex="1" parent="{cluster_id}">
          <mxGeometry x="{node_x}" y="{node_y}" width="120" height="60" as="geometry"/>
        </mxCell>"""
                )

                # Store position for edge creation
                positions[node_id] = {
                    "x": cluster_x + node_x + 60,
                    "y": cluster_y + node_y + 30,
                }

        # Process standalone nodes
        standalone_nodes = spec.get("nodes", [])
        standalone_y = y_offset + len(clusters) * (cluster_height + 50) // 3 + 100

        for i, node in enumerate(standalone_nodes):
            node_id = node.get("id", f"standalone_{cell_counter}")
            cell_counter += 1

            node_label = node.get("label", node_id)
            node_type = node.get("type", "server")
            provider = node.get("provider", "aws")

            # Position standalone nodes
            node_x = 50 + (i % 4) * 200
            node_y = standalone_y + (i // 4) * 100

            shape_style = self._get_drawio_shape_style(provider, node_type)

            xml_parts.append(
                f"""        <mxCell id="{node_id}" value="{self._escape_xml(node_label)}" style="{shape_style}" vertex="1" parent="1">
          <mxGeometry x="{node_x}" y="{node_y}" width="120" height="60" as="geometry"/>
        </mxCell>"""
            )

            positions[node_id] = {"x": node_x + 60, "y": node_y + 30}

        # Process edges
        edges = spec.get("edges", [])
        for edge in edges:
            if len(edge) >= 2:
                source_id = edge[0]
                target_id = edge[1]
                edge_label = edge[2] if len(edge) > 2 else ""

                if source_id in positions and target_id in positions:
                    edge_id = f"edge_{cell_counter}"
                    cell_counter += 1

                    xml_parts.append(
                        f"""        <mxCell id="{edge_id}" value="{self._escape_xml(edge_label)}" style="edgeStyle=orthogonalEdgeStyle;rounded=0;orthogonalLoop=1;jettySize=auto;html=1;exitX=1;exitY=0.5;exitDx=0;exitDy=0;entryX=0;entryY=0.5;entryDx=0;entryDy=0;" edge="1" parent="1" source="{source_id}" target="{target_id}">
          <mxGeometry relative="1" as="geometry"/>
        </mxCell>"""
                    )

        # Add export info
        xml_parts.append(
            f"""        <mxCell id="export-info" value="Exported from AAA System - {datetime.now().strftime('%Y-%m-%d %H:%M')}" style="text;html=1;strokeColor=none;fillColor=none;align=right;verticalAlign=middle;whiteSpace=wrap;rounded=0;fontSize=10;fontColor=#666666;" vertex="1" parent="1">
          <mxGeometry x="969" y="800" width="200" height="20" as="geometry"/>
        </mxCell>"""
        )

        # Close XML structure
        xml_parts.extend(
            ["      </root>", "    </mxGraphModel>", "  </diagram>", "</mxfile>"]
        )

        return "\n".join(xml_parts)

    def _get_drawio_shape_style(self, provider: str, component_type: str) -> str:
        """Get Draw.io shape style for cloud components."""

        # AWS shapes
        aws_shapes = {
            "lambda": "shape=mxgraph.aws4.lambda_function;fillColor=#FF9900;strokeColor=#FF9900;",
            "ec2": "shape=mxgraph.aws4.ec2;fillColor=#FF9900;strokeColor=#FF9900;",
            "rds": "shape=mxgraph.aws4.rds;fillColor=#3F48CC;strokeColor=#3F48CC;",
            "dynamodb": "shape=mxgraph.aws4.dynamodb;fillColor=#3F48CC;strokeColor=#3F48CC;",
            "s3": "shape=mxgraph.aws4.s3;fillColor=#569A31;strokeColor=#569A31;",
            "apigateway": "shape=mxgraph.aws4.api_gateway;fillColor=#FF4F8B;strokeColor=#FF4F8B;",
            "sqs": "shape=mxgraph.aws4.sqs;fillColor=#FF4F8B;strokeColor=#FF4F8B;",
            "sns": "shape=mxgraph.aws4.sns;fillColor=#FF4F8B;strokeColor=#FF4F8B;",
        }

        # GCP shapes
        gcp_shapes = {
            "functions": "shape=mxgraph.gcp2.cloud_functions;fillColor=#4285F4;strokeColor=#4285F4;",
            "gce": "shape=mxgraph.gcp2.compute_engine;fillColor=#4285F4;strokeColor=#4285F4;",
            "sql": "shape=mxgraph.gcp2.cloud_sql;fillColor=#4285F4;strokeColor=#4285F4;",
            "firestore": "shape=mxgraph.gcp2.firestore;fillColor=#4285F4;strokeColor=#4285F4;",
            "gcs": "shape=mxgraph.gcp2.cloud_storage;fillColor=#4285F4;strokeColor=#4285F4;",
        }

        # Azure shapes
        azure_shapes = {
            "functions": "shape=mxgraph.azure.azure_functions;fillColor=#0078D4;strokeColor=#0078D4;",
            "vm": "shape=mxgraph.azure.virtual_machine;fillColor=#0078D4;strokeColor=#0078D4;",
            "sql": "shape=mxgraph.azure.sql_database;fillColor=#0078D4;strokeColor=#0078D4;",
            "cosmosdb": "shape=mxgraph.azure.cosmos_db;fillColor=#0078D4;strokeColor=#0078D4;",
            "storage": "shape=mxgraph.azure.storage;fillColor=#0078D4;strokeColor=#0078D4;",
        }

        # Generic shapes for unknown types
        generic_shapes = {
            "server": "shape=mxgraph.basic.server;fillColor=#d5e8d4;strokeColor=#82b366;",
            "database": "shape=mxgraph.basic.database;fillColor=#f8cecc;strokeColor=#b85450;",
            "api": "shape=mxgraph.basic.cloud;fillColor=#dae8fc;strokeColor=#6c8ebf;",
        }

        # Select appropriate shape based on provider
        if provider == "aws" and component_type in aws_shapes:
            return (
                aws_shapes[component_type]
                + "html=1;verticalLabelPosition=bottom;verticalAlign=top;align=center;"
            )
        elif provider == "gcp" and component_type in gcp_shapes:
            return (
                gcp_shapes[component_type]
                + "html=1;verticalLabelPosition=bottom;verticalAlign=top;align=center;"
            )
        elif provider == "azure" and component_type in azure_shapes:
            return (
                azure_shapes[component_type]
                + "html=1;verticalLabelPosition=bottom;verticalAlign=top;align=center;"
            )
        else:
            # Fallback to generic shapes
            generic_type = "server"
            if "database" in component_type.lower() or "db" in component_type.lower():
                generic_type = "database"
            elif "api" in component_type.lower() or "gateway" in component_type.lower():
                generic_type = "api"

            return (
                generic_shapes.get(generic_type, generic_shapes["server"])
                + "html=1;verticalLabelPosition=bottom;verticalAlign=top;align=center;"
            )

    def _escape_xml(self, text: str) -> str:
        """Escape text for XML content."""
        if not text:
            return ""

        return (
            text.replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;")
            .replace("'", "&#39;")
        )

    def export_multiple_formats(
        self, diagram_data: Dict[str, Any], diagram_title: str, output_path: str
    ) -> List[str]:
        """
        Export diagram in multiple formats for maximum compatibility.
        Returns list of created file paths.
        """
        exported_files = []

        try:
            # Determine diagram type and export accordingly
            if "mermaid_code" in diagram_data:
                # Mermaid diagram
                mermaid_code = diagram_data["mermaid_code"]

                # Export as Draw.io
                drawio_file = self.export_mermaid_diagram(
                    mermaid_code, diagram_title, output_path
                )
                exported_files.append(drawio_file)

                # Also export raw Mermaid for direct import
                mermaid_file = f"{output_path}.mmd"
                with open(mermaid_file, "w", encoding="utf-8") as f:
                    f.write(mermaid_code)
                exported_files.append(mermaid_file)

            elif "infrastructure_spec" in diagram_data:
                # Infrastructure diagram
                infrastructure_spec = diagram_data["infrastructure_spec"]

                # Export as Draw.io
                drawio_file = self.export_infrastructure_diagram(
                    infrastructure_spec, diagram_title, output_path
                )
                exported_files.append(drawio_file)

                # Also export JSON specification
                json_file = f"{output_path}.json"
                with open(json_file, "w", encoding="utf-8") as f:
                    json.dump(infrastructure_spec, f, indent=2)
                exported_files.append(json_file)

            self.app_logger.info(
                f"Exported diagram in {len(exported_files)} formats: {exported_files}"
            )
            return exported_files

        except Exception as e:
            self.app_logger.error(f"Failed to export multiple formats: {e}")
            raise
