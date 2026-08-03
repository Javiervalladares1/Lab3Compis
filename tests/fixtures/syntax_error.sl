# Missing the closing brace of the index page -> syntax error.
site "broken-site" {
  title = "Broken"

  page "index" {
    hero = "This page never closes"
}
