# Changelog

## Unreleased

- FIX: parse the `TestTime`/`StepTime` columns of the "Maccor Export 1" and
  "MIMS Client 2" text formats, which are exported as duration strings
  (`"Nd HH:MM:SS[,ff]"`), into a numeric number of seconds. Adds the public
  helper `maccor_utility.helper_functions.parse_duration_to_seconds`.

## Version 0.1 (development)

- Feature A added
- FIX: nasty bug #1729 fixed
- add your changes here!
