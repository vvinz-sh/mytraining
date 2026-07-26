from fastmcp import FastMCP
import git
import hashlib

mcp = FastMCP("git-push-perso")

def _commits_a_pousser(repo_path: str) -> list[str]:
    repo = git.Repo(repo_path)
    return [c.hexsha for c in repo.iter_commits("@{u}..")]

def _token(hashes: list[str]) -> str:
    return hashlib.sha256("".join(hashes).encode()).hexdigest()

@mcp.tool()
def git_push_preview(repo_path: str) -> str:
    """Montre ce qui serait poussé, sans rien modifier. Retourne aussi
    un token à fournir tel quel à git_push_confirm."""
    hashes = _commits_a_pousser(repo_path)
    if not hashes:
        return "Rien à pousser : la branche locale est à jour avec le remote."

    repo = git.Repo(repo_path)
    resume = f"{len(hashes)} commit(s) à pousser :\n"
    for h in hashes:
        resume += f"- {h[:7]} : {repo.commit(h).summary}\n"
    resume += f"\nToken à utiliser pour confirmer : {_token(hashes)}"
    return resume

@mcp.tool()
def git_push_confirm(repo_path: str, token: str) -> str:
    """Exécute le push réel — uniquement si le token correspond
    exactement à ce qui serait poussé À CE MOMENT PRÉCIS."""
    hashes_actuels = _commits_a_pousser(repo_path)
    if _token(hashes_actuels) != token:
        return ("Refusé : l'état du dépôt a changé depuis l'aperçu "
                "(nouveau commit, ou plus rien à pousser). "
                "Relance git_push_preview.")

    repo = git.Repo(repo_path)
    resultat = repo.remote(name="origin").push()
    return f"Push effectué : {resultat[0].summary if resultat else 'OK'}"

if __name__ == "__main__":
    mcp.run()
