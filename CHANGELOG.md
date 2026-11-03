# Changelog

## Version 1.5.0

- FIX: parse the `TestTime`/`StepTime` columns of the "Maccor Export 1" and
  "MIMS Client 2" text formats, which are exported as duration strings
  (`"Nd HH:MM:SS[,ff]"`), into a numeric number of seconds. Adds the public
  helper `maccor_utility.helper_functions.parse_duration_to_seconds`.
- FIX: read the file header with the encoding the format declares. It was read
  with the platform default, so a cp1252 export (MIMS Client 2) raised
  `UnicodeDecodeError` on any system whose default is UTF-8.
- Python 3.10 is now the minimum; the runner images no longer carry 3.8.

## Version 0.1 (development)

- Feature A added
- FIX: nasty bug #1729 fixed
- add your changes here!
