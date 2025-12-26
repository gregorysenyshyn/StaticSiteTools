import os
import glob
import click
from botocore.exceptions import ClientError

try:
    import frontmatter
except ImportError:
    frontmatter = None

def get_email_templates(directory="email_templates"):
    """
    Scans the specified directory for email template files.
    Returns a dictionary: { 'template_name': { 'Subject': ..., 'Text': ..., 'Html': ... } }
    """
    templates = {}
    # Support .html and .md files
    files = glob.glob(os.path.join(directory, "*.html")) + glob.glob(os.path.join(directory, "*.md"))

    if not files:
        return templates

    for filepath in files:
        filename = os.path.basename(filepath)
        template_name = os.path.splitext(filename)[0]

        try:
            if frontmatter is None:
                raise ImportError("python-frontmatter is required to parse templates. Please install it.")

            post = frontmatter.load(filepath)

            subject = post.metadata.get('subject')
            text_content = post.metadata.get('text')
            html_content = post.content

            if not subject:
                click.echo(f"Warning: Skipping {filename} - Missing 'subject' in frontmatter.")
                continue

            # If text content is missing, we could try to strip HTML, but for now let's just warn or leave empty
            # SES requires both Text and Html usually for best practice, but technically one might be optional depending on strictness.
            # However, create_email_template params: TemplateContent={ 'Subject': ..., 'Text': ..., 'Html': ... }
            if not text_content:
                # automated fallback or warning?
                # User said: "store subject and plaintext versions of emails in frontmatter"
                # So we expect it there.
                pass

            templates[template_name] = {
                'Subject': subject,
                'Text': text_content if text_content else "",
                'Html': html_content
            }

        except Exception as e:
            click.echo(f"Error parsing {filename}: {e}")

    return templates

def list_ses_templates(ses_client):
    """
    Generator that yields all SES templates, handling pagination.
    """
    paginator = ses_client.get_paginator('list_email_templates')
    for page in paginator.paginate():
        for template in page['TemplatesMetadata']:
            yield template['TemplateName']

def sync_templates(ses_client, directory="email_templates", delete_orphans=False):
    """
    Syncs local templates to SES.
    """
    if not os.path.isdir(directory):
        click.echo(f"Directory '{directory}' not found.")
        return

    local_templates = get_email_templates(directory)
    if not local_templates:
        click.echo(f"No templates found in '{directory}'.")
        return

    click.echo(f"Found {len(local_templates)} local templates.")

    # Get existing SES templates to decide Create vs Update
    existing_templates = set(list_ses_templates(ses_client))

    for name, content in local_templates.items():
        template_content = {
            'Subject': content['Subject'],
            'Html': content['Html']
        }
        if content['Text']:
            template_content['Text'] = content['Text']

        try:
            if name in existing_templates:
                click.echo(f"Updating template: {name}")
                ses_client.update_email_template(
                    TemplateName=name,
                    TemplateContent=template_content
                )
            else:
                click.echo(f"Creating template: {name}")
                ses_client.create_email_template(
                    TemplateName=name,
                    TemplateContent=template_content
                )
        except ClientError as e:
            click.echo(f"Failed to sync {name}: {e}")

    # Handle Deletions
    if delete_orphans:
        orphans = existing_templates - set(local_templates.keys())
        if orphans:
            click.echo("\nFound orphaned templates in SES (not in local):")
            for orphan in orphans:
                click.echo(f" - {orphan}")

            if click.confirm("Delete these templates from SES?"):
                for orphan in orphans:
                    try:
                        ses_client.delete_email_template(TemplateName=orphan)
                        click.echo(f"Deleted {orphan}")
                    except ClientError as e:
                        click.echo(f"Failed to delete {orphan}: {e}")
        else:
            click.echo("No orphaned templates found.")

def list_templates(ses_client):
    """
    Lists all templates in SES.
    """
    click.echo("Fetching templates from SES...")
    templates = list(list_ses_templates(ses_client))
    if not templates:
        click.echo("No templates found in SES.")
    else:
        click.echo(f"\nSES Templates ({len(templates)}):")
        for t in sorted(templates):
            click.echo(f" - {t}")
