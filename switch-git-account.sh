#!/bin/bash

# Git Account Switcher Script
# Usage: ./switch-git-account.sh [account-name]

echo "🔄 Git Account Switcher"

case "$1" in
    "blureonlabs"|"main")
        echo "Switching to main account: blureonlabs"
        git config user.name "blureonlabs"
        git config user.email "blureonlabs@gmail.com"
        echo "✅ Switched to main account"
        ;;
    "harp"|"hariprasad"|"Harp0859")
        echo "Switching to Hariprasad Nivas (Harp0859)"
        git config user.name "Hariprasad Nivas"
        git config user.email "hariprasad@example.com"
        echo "✅ Switched to Hariprasad Nivas"
        ;;
    "team2"|"dev2")
        echo "Switching to team member 2"
        git config user.name "Team Member 2"
        git config user.email "team2@example.com"
        echo "✅ Switched to team member 2"
        ;;
    *)
        echo "Usage: ./switch-git-account.sh [account-name]"
        echo "Available accounts:"
        echo "  blureonlabs (main)"
        echo "  harp (hariprasad)"
        echo "  team2 (dev2)"
        echo ""
        echo "Current config:"
        echo "  Name: $(git config user.name)"
        echo "  Email: $(git config user.email)"
        exit 1
        ;;
esac

echo ""
echo "Current Git config:"
echo "  Name: $(git config user.name)"
echo "  Email: $(git config user.email)"
