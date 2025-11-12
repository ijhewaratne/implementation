#!/usr/bin/env python3

# Read the file
with open("optimize/diameter_optimizer.py", "r") as f:
    lines = f.readlines()

# Find the line with the path_stats assignment
for i, line in enumerate(lines):
    if "path_stats[path_id] = {" in line:
        print(f"Found path_stats assignment at line {i+1}")

        # Insert the supply segment filtering logic before this line
        new_lines = lines[: i - 1]  # Lines before the for loop

        # Add the for loop with filtering
        new_lines.extend(
            [
                "            for path_id, path_segments in path_groups.items():\n",
                "                # Only process paths that contain supply segments\n",
                "                supply_segments = [seg for seg in path_segments if seg.is_supply]\n",
                "                if not supply_segments:\n",
                "                    continue  # Skip return-only paths\n",
                "                \n",
                "                # Only evaluate supply segments for path head\n",
                "                supply_only_segments = [seg for seg in path_segments if seg.is_supply]\n",
                "                dp_path, max_V_dot = self._eval_path_head(supply_only_segments)\n",
                "                \n",
                "                # Only add to path_stats if there are supply segments and non-zero pressure drop\n",
                "                if supply_segments and dp_path > 0:\n",
                "                    path_stats[path_id] = {\n",
                '                        "dp_Pa": dp_path,\n',
                '                        "V_dot_peak_m3s": max_V_dot\n',
                "                    }\n",
                "                \n",
            ]
        )

        # Add the rest of the lines after the path_stats block
        # Find where the path_stats block ends
        j = i
        while j < len(lines) and "}" not in lines[j]:
            j += 1
        j += 1  # Skip the closing brace

        # Add the rest of the logic
        new_lines.extend(
            [
                "                if dp_path > worst_dp:\n",
                "                    worst_dp = dp_path\n",
                "                    worst_max_V_dot = max_V_dot\n",
                "                    worst_path_id = path_id\n",
            ]
        )

        # Add the remaining lines
        new_lines.extend(lines[j:])

        # Write the file back
        with open("optimize/diameter_optimizer.py", "w") as f:
            f.writelines(new_lines)

        print("Fix applied successfully!")
        break
else:
    print("Could not find path_stats assignment")
