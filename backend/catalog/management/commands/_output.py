def report(command, result):
    """Print an UpsertResult summary for a management command."""
    style = command.style
    verb = 'Created' if result.game_created else 'Updated'
    command.stdout.write(style.SUCCESS(f'{verb} "{result.game.title}" ({result.game.slug})'))
    if not result.game.is_reviewed:
        command.stdout.write(style.WARNING('  not reviewed yet: tick "reviewed" in the admin to show it on the site'))
    command.stdout.write(
        f'  achievements: {len(result.created)} new, {len(result.updated)} updated, {len(result.deleted)} deleted'
    )
    if result.kept_with_progress:
        command.stdout.write(
            style.WARNING(
                f'  kept {len(result.kept_with_progress)} missing achievement(s) that users have unlocked: '
                + ', '.join(result.kept_with_progress)
            )
        )
