# CANTAMEN to ical

[CANTAMEN](https://cantamen.de/) offers a nice App and Web-App to manage car sharing bookings.
While the user receives and iCAL file per mail after each booking, this option must be configured by the car sharing provider, this can be a pain to integrate into the user's calender and is not automatically updated if the booking is canceled or modified.

This Flask Webapp uses the official CANTAMEN APIs to generate an iCAL file with the bookings of the user in the next 6 months.
Running the Webapp on your favorite full-stack provide (e.g. heroku, fly.io or pythonanywhere) or your own server allows to include the URL in your favorite calendar application as external calendar.
Please note that the resulting calendar is publicly available.

The username is expected as URL GET parameter in base64 encoding, e.g. https://[provider_url]/cantamen_to_ical?user=dXNlcm5hbWU=.
Encode your username via
```
import base64
base64.urlsafe_b64encode("[username]".encode())
```
The password for the user is read from environment variables `CANTAMEN_PWD_[base64_encoded_username]`.
The API key needs to be provide in the environment variable `CANTAMEN_API_KEY`.
The key can be obtained by opening the CANTAMEN Webapp of your provider, and inspect header `X-API-Key` in any request to https://de1.cantamen.de/casirest/v3/.

## Contribution
Use a pull request.