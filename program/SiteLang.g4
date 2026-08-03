grammar SiteLang;

site: 'site' STRING '{' siteBody '}' EOF;
siteBody: (siteAttr | page)*;
siteAttr: IDENTIFIER '=' expr;
page: 'page' STRING '{' pageBody '}';
pageBody: pageAttr*;
pageAttr: IDENTIFIER '=' expr;
expr: STRING | NUMBER | BOOLEAN;

BOOLEAN: 'true' | 'false';
NUMBER: [0-9]+ ('.' [0-9]+)?;
STRING: '"' ('\\' . | ~["\\])* '"';
IDENTIFIER: [a-zA-Z_][a-zA-Z_0-9\-]*;
COMMENT: '#' ~[\r\n]* -> skip;
WS: [ \t\r\n]+ -> skip;
