IDEA :

GitHub Pages deploys from only **one source** (branch/folder) per repository, so the live site URL stays the same. You can't host production and beta simultaneously at different subpaths without extra setup (like GitHub Actions).

A simple, safe approach uses branch renaming to switch to the beta temporarily, show it to users at the live URL, and easily revert if needed.

### Recommended Approach: Temporary Beta Switch via Branch Rename

This preserves your current production site code while letting you deploy the beta to the live URL.

1. **Identify your current Pages source**  
   Go to repository **Settings > Pages**. Note the branch (e.g., `gh-pages`, `main`, or another) and folder (usually `/ (root)` or `/docs`).

2. **Rename the current production branch (to preserve it)**

   - In GitHub UI: Go to the **Branches** tab, click the pencil icon next to the branch, and rename it (e.g., to `gh-pages-prod` or `main-prod`).
   - Or locally:
     ```
     git checkout current-branch-name
     git branch -m new-prod-name  # e.g., gh-pages-prod
     git push origin :old-branch-name new-prod-name  # Delete old remote and push new
     ```
     After renaming, your live site may temporarily show a 404 until you set a new source—act quickly.

3. **Create a new branch for the beta**

   - Create and checkout a new branch with the same name as the old one (e.g., `gh-pages`).
   - Base it on your development branch with the changes:
     ```
     git checkout your-changes-branch
     git branch gh-pages  # Or main, matching the original source name
     git push origin gh-pages
     ```

4. **Update Pages settings to the new branch**

   - Repository **Settings > Pages > Branch**: Select the new branch (same name as before) and folder. Save.
   - GitHub will deploy the beta version automatically (may take a few minutes).
   - Your live GitHub Pages URL now shows the beta—share it with users for feedback.

5. **Revert to production if needed**
   - Rename the beta branch away (e.g., to `gh-pages-beta`).
   - Rename the preserved prod branch back to the original name (e.g., `gh-pages-prod` → `gh-pages`).
   - Or in Settings > Pages, switch back to the prod branch.
   - The site reverts to the original version.

This method is straightforward, requires no workflows, and works on all plans.

### Better Long-Term Option: Persistent Beta (Without Affecting Live URL)

If you want production at the root URL and beta at a subpath like `your-site.com/beta` simultaneously:

- Set up a **GitHub Actions** workflow to build/deploy the beta to a subdirectory on your production branch.
- Use popular actions like [peaceiris/actions-gh-pages](https://github.com/peaceiris/actions-gh-pages) (supports `destination_dir: beta`).
- Trigger it on pushes to your changes branch.
- Production stays untouched at the root.

This needs a `.github/workflows/deploy.yml` file—check the action's docs for examples.

If your site uses Jekyll or another builder, set a `baseurl: /beta` in config for subpath deploys to handle links correctly.

For details, see GitHub Docs on [configuring Pages source](https://docs.github.com/en/pages/getting-started-with-github-pages/configuring-a-publishing-source-for-your-github-pages-site) and [renaming branches](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-branches-in-your-repository/renaming-a-branch).

Let me know your current Pages branch/setup or if you use Actions already—I can give more tailored steps!
