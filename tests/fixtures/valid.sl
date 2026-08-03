# A syntactically valid and semantically correct site.
site "test-site" {
  title       = "Test Site"
  description = "A site used by the test suite"
  theme       = "light"

  page "index" {
    hero    = "Hello <world> & \"friends\""
    about   = "About text"
    contact = "test@example.com"
  }
}
