async def setup(bot):
    from .cog import setup as setup_cog

    await setup_cog(bot)

