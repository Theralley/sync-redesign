   // s2am tiles: one big tile for the first app, up to three small ones, and "All apps",
   // which shows the original list. Pictures: <rootPath>Apps/Info/SyncApps/Tiles/<native>[-big].png
   function showTiles(appObjects)
   {
      this._tileObjects = appObjects;
      var slots = [[170,106,295,300],[475,106,155,145],[640,106,155,145],[475,261,155,145],[640,261,155,145]];
      var apps = new Array();
      var i = 0;
      while(i < appObjects.length)
      {
         if(appObjects[i] != undefined && appObjects[i].installedAppName != "" && this.isNativeApp(appObjects[i].installedAppName))
         {
            apps.push(appObjects[i]);
         }
         i = i + 1;
      }
      if(this.pThis.s2amTiles != undefined)
      {
         this.pThis.s2amTiles.removeMovieClip();
      }
      this.pThis.compScreen._visible = false;
      var depth = this.pThis.getNextHighestDepth();
      if(depth > 1048000)
      {
         depth = 1048000;
      }
      var host = this.pThis.createEmptyMovieClip("s2amTiles",depth);
      var count = apps.length < 4 ? apps.length : 4;
      i = 0;
      while(i < count)
      {
         this.addTile(host,i,slots[i],apps[i].installedAppName);
         i = i + 1;
      }
      this.addTile(host,count,slots[count],"s2am.AllApps");
   }
   function addTile(host, index, slot, appName)
   {
      var tile = host.createEmptyMovieClip("tile" + index,index + 1);
      tile._x = slot[0];
      tile._y = slot[1];
      tile.beginFill(1316378,100);
      tile.moveTo(0,0);
      tile.lineTo(slot[2],0);
      tile.lineTo(slot[2],slot[3]);
      tile.lineTo(0,slot[3]);
      tile.lineTo(0,0);
      tile.endFill();
      var picture = tile.createEmptyMovieClip("picture",1);
      picture.loadMovie(this.rootPath + "Apps/Info/SyncApps/Tiles/" + (appName == "s2am.AllApps" ? "AllApps" : appName) + (index == 0 ? "-big" : "") + ".png");
      tile.appName = appName;
      tile.owner = this;
      tile.onPress = function()
      {
         this._alpha = 60;
      };
      tile.onReleaseOutside = function()
      {
         this._alpha = 100;
      };
      tile.onRelease = function()
      {
         this._alpha = 100;
         this.owner.tileSelected(this.appName);
      };
   }
   function tileSelected(appName)
   {
      if(appName == "s2am.AllApps")
      {
         this.showList();
         return undefined;
      }
      this.getEventFromList("LeftSelected",{leftAppName:appName});
   }
   function showList()
   {
      if(this.pThis.s2amTiles != undefined)
      {
         this.pThis.s2amTiles.removeMovieClip();
      }
      this.pThis.compScreen._visible = true;
      super.FillTheList(this._tileObjects);
   }
   function destroy()
   {
      if(this.pThis.s2amTiles != undefined)
      {
         this.pThis.s2amTiles.removeMovieClip();
      }
      super.destroy();
   }
