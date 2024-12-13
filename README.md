The script provides the following options:

1. **List all playlists**
   - Shows all your YouTube playlists
   - Displays title, ID, video count, and description

2. **Create new playlist**
   - Create a new playlist with custom:
     - Title
     - Description (optional)
     - Privacy status (public/private/unlisted)

3. **Delete playlist**
   - Delete a specific playlist by ID
   - Requires confirmation

4. **Delete ALL playlists**
   - Bulk delete all playlists
   - Requires typing 'DELETE ALL' to confirm

5. **Create BoC Albums playlist**
   - Creates a chronological Boards of Canada playlist
   - Includes all major releases and EPs
   - Searches for full album videos
   - Allows manual selection of correct versions

6. **Exit**
   - Exits the application

## Boards of Canada Playlist

The BoC playlist creator includes the following releases in chronological order:
- Twoism (1995)
- Hi Scores EP (1996)
- Music Has the Right to Children (1998)
- In A Beautiful Place Out In The Country EP (2000)
- Geogaddi (2002)
- The Campfire Headphase (2005)
- Trans Canada Highway EP (2006)
- Tomorrow's Harvest (2013)

## Security Notes

- The `client_secret.json` file contains your OAuth 2.0 credentials and should never be shared or committed to version control
- Authentication tokens are cached in `token.pickle` for convenience
- Both sensitive files are automatically excluded via `.gitignore`

## Troubleshooting

If you encounter authentication issues:
1. Verify your `client_secret.json` is in the correct location
2. Delete `token.pickle` to force re-authentication
3. Ensure you've enabled the YouTube Data API in Google Cloud Console
4. Check that your OAuth consent screen is properly configured

## Contributing

Feel free to submit issues and enhancement requests!

## License

Free to use and modify.