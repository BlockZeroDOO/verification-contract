from __future__ import annotations


def swagger_ui_html(title: str, openapi_url: str) -> str:
    return f"""<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>{title}</title>
    <link rel="stylesheet" href="https://unpkg.com/swagger-ui-dist@5/swagger-ui.css">
    <style>
      html {{
        box-sizing: border-box;
        overflow-y: scroll;
      }}
      *,
      *:before,
      *:after {{
        box-sizing: inherit;
      }}
      body {{
        margin: 0;
        background: #f6f8fb;
      }}
    </style>
  </head>
  <body>
    <div id="swagger-ui"></div>
    <script src="https://unpkg.com/swagger-ui-dist@5/swagger-ui-bundle.js"></script>
    <script>
      window.onload = function() {{
        window.ui = SwaggerUIBundle({{
          url: '{openapi_url}',
          dom_id: '#swagger-ui',
          deepLinking: true,
          presets: [SwaggerUIBundle.presets.apis],
          layout: 'BaseLayout'
        }});
      }};
    </script>
  </body>
</html>
"""
