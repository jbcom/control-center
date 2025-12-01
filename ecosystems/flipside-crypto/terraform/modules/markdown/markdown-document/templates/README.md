%{ if title != null ~}
# ${title(replace(replace(title, "-", " "), "_", " "))}

%{ endif ~}
%{ if description != null ~}

${description}

%{ endif ~}
%{ if index_html_data != "" ~}

${section_heading_level} Index

${index_html_data}
%{ endif ~}
%{ for section_data in sections ~}

${section_heading_level} ${section_data["heading"]}

%{ if section_data["description"] != null ~}

${section_data["description"]}

%{ endif ~}
%{ for snippet_data in section_data["snippets"] ~}
%{ if snippet_data["content"] != null ~}

${nested_section_heading_level} ${snippet_data["heading"]}

${snippet_data["content"]}

%{ endif ~}
%{ endfor ~}
%{ for cur_table, table_data in section_data["tables"] ~}

%{ if table_data["title"] != null ~}

${nested_section_heading_level} ${table_data["heading"]}
%{ endif ~}
%{ if table_data["description"] != null ~}

${table_data["description"]}

%{ endif ~}

<table>
<tr>
%{ for table_header in table_metadata[section_data["title"]][cur_table]["headers"] ~}
<th>${title(replace(replace(table_header, "-", " "), "_", " "))}</th>
%{ endfor ~}
</tr>
%{ for cur_row in range(0, table_metadata[section_data["title"]][cur_table]["row_count"]) ~}
<tr>
%{ for column_data in table_data["columns"] ~}
<td>${try(chomp(column_data["rows"][cur_row]), "")}</td>
%{ endfor ~}
</tr>
%{ endfor ~}

</table>
%{ endfor ~}
%{ endfor ~}