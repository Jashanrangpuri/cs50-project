# TOOLIFY

### Video Demo: [Toolify Demo](https://youtu.be/LwfvrAVLXpM)

### Description:

#### Overview:

**Toolify** is a web web application that integrates with the Spotify API to offer advanced playlist management and listening analytics. This final Project for CS50x course was built using **Python**, **Flask**, **HTML**, **CSS,** and **JavaScript**. Toolify allows users to log in with their Spotify accounts and perform a variety of useful tasks.

My motivation to build this tool was that I wanted an easy way to back up my playlists and track my listening habits over time and gain deeper insight into my music preferences.

#### Key features include:

-   Convert Spotify playlists to CSV for easy **Backup** and sharing.
-   **Restore playlists** from CSV, enabling quick recovery or duplication of playlists.
-   **Analyze playlist** content, offering insights like track popularity, top tracks and more. You can analyze your Playlists, if logged in or enter url of a public Playlist.
-   View **personalized statistics** like top artists and tracks based on your listening history.

Toolify uses both client and user authorization through the Spotify API, making it a secure and personalized experience. Some features of Toolify are available without logging in, such as analyzing public playlists via URL. However, to access full functionality—including backup, restore, and personal analytics—you must authenticate with your Spotify account.

---

### How to use:

#### Backup

-   After logging in, you can navigate to the Backup page to view all your playlists and download them as CSV files for easy storage or backup.

#### Restore

If you have a CSV file formatted correctly, you can restore playlists back into Spotify:

-   Navigate to the Restore page.
-   Upload your CSV file.
-   Ensure the file is not too large and contains the required columns.
-   Follow the on-page instructions for successful restoration.

#### Playlist Analysis

Toolify can analyze playlists to give you insights like:

-   Top artists and tracks.
-   Track popularity.
-   Other aggregated playlist statistics.

You can analyze your own playlists (while logged in) or input the URL of any public Spotify playlist.

-   You can also view your top tracks and artists from the past month, the last 4 months, or the past year, giving you insights into your listening habits over time.

One of the biggest challenges I faced was learning how to work with the Spotify API, especially understanding the authentication flow and how to parse the API documentation effectively. However, it was a rewarding experience that deepened my understanding of web development, REST APIs, user-based data access. Building this project deepened my appreciation for well-written documentation and highlighted the importance of thoroughly reviewing it before starting development. It saved time, clarified uncertainties, and ultimately improved the quality of my implementation.

Overall, Toolify was a rewarding and practical project that combined my interests in music and coding. It helped me solidify core web development concepts and taught me how to integrate external services into my own applications.

Unfortunately, due to recent changes in the Spotify API, certain audio features such as energy, valence and tempo are no longer accessible without elevated permissions. Additionally, making the app publicly available now requires submitting it for approval through Spotify’s developer application process. These limitations restricted the overall scope of the project.

This application can only be used by users whose email addresses have been added to the User Management list in the Spotify Developer Dashboard. If you would like to use this app, consider creating your own Spotify developer application and adding your Client ID and Client Secret to the **.env** file in this project. This ensures the app functions correctly and securely with your credentials.

#### Configuration

Follow these steps:

1. Create a Spotify Developer app:

    - Visit the Spotify Developer Dashboard
    - Log in and create a new app.
    - Note your Client ID and Client Secret.

2. Add authorized redirect URIs:

    - Add http://127.0.0.1:5000/callback to the Redirect URIs in your app settings.

3. Replace CLIENT_ID and CLIENT_SECRET with your Client ID and secret in the .env file located in the **toolify** folder

---

### Technical Details

#### Technologies Used:

-   **Backend** : Python, Flask
-   **Frontend** : HTML, CSS, JavaScript
-   **API** : Spotify Web API with OAuth 2.0 authentication
-   **Data** : Playlist data processed in CSV format for export and import
-   **Spotify API Integration** : Toolify interacts with Spotify’s API to:
    -   Fetch user playlists and tracks
    -   Export playlists as CSV files
    -   Create playlists and add tracks during restore
    -   Retrieve user top tracks and artists
    -   Analyze playlists by track metadata
    -   Authentication uses Spotify’s OAuth 2.0 flow with both client and user authorization to securely access user data.

---

### Future Improvements

-   Automate user onboarding and approval to streamline access.
-   Implement advanced audio feature analysis if API permissions become available or use integrate other APIs.
-   Add playlist collaboration and sharing features.
-   Improve UI/UX for better usability and mobile responsiveness.
