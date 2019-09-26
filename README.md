# `ra-snoop`, a janky way to track changes to residentadvisor.net artist listings

https://www.residentadvisor.net has fairly comprehensive listings for lots of
electronic music artists but (as far as I can tell) no means to be notified of
changes. This dumb script does that. Hook it up to `cron` and `mail` and you're
done.

## Usage

```bash
$ ./snoop.py deadmau5
==> deadmau5

+2019-03-29  Ultra                                     Miami, USA
+2019-08-15  Barcelona Sutton                          Barcelona, Spain
+2019-08-16  Port Du Soleil                            Gothenburg, Sweden
+2019-08-22  Creamfields                               North, United Kingdom
```

## Bugs etc

Many, probably.
