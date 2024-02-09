# CANTAMEN to ical

[CANTAMEN](https://cantamen.de/) offers a nice Anrdoid/iOS App and Web-App to manage car sharing bookings.
While the user receives an iCal file per mail after each booking, this option must be configured by the car sharing provider.
In addition, integrating an iCal into your calender for each booking can be cumbersome and most importantly, it is not automatically updated in case the booking is canceled or modified.

This Flask App uses the official CANTAMEN APIs to generate an iCal file with the bookings of the user in the upcoming 6 months.
Running the Webapp on your favorite full-stack provide (e.g. heroku, [fly.io](https://fly.io/docs/languages-and-frameworks/python/) or pythonanywhere) or your own server allows to include the URL in most calendar applications as external calendar.
Please note that the resulting calendar is publicly available under the URL.

The username is expected as URL GET parameter in base64 encoding, e.g. https://[provider_url]/cantamen_to_ical?user=dXNlcm5hbWU=.
Encode your username via
```
import base64
base64.urlsafe_b64encode("[username]".encode())
```
or use an online tool.
The password for the user is read from environment variables `CANTAMEN_PWD_[base64_encoded_username]`.
The API key needs to be provide in the environment variable `CANTAMEN_API_KEY`.
The API key can be obtained by opening the CANTAMEN Web-App and inspect the header `X-API-Key` in any request to https://de1.cantamen.de/casirest/v3.

## Contribution
Use a pull request.
