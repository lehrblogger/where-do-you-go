/* Generate ../etc/dots/dot*.png for use by gheat.
 *
 * Open ../etc/dots/master.psd in PhotoShop, and then run this script (File > 
 * Automate > Scripts; if using PhotoShop version 7 you must have the scripting 
 * plugin installed).
 *
 */


if (documents.length == 0)
{
  alert("Please open a master dot file before running this script.");
}
else
{
    var w = activeDocument.width;
    var h = activeDocument.height;
    var step_w = w / 31;
    var step_h = h / 31;

    //alert("(" + step_w + ", " + step_h + "), (" + w + ", " + h + ")");

    for(var i=0; i < 31; i++)
    {
        //if (i > 3) break; 
        new_w = w - (step_w * i);
        new_h = h - (step_h * i);
        //alert(i + ": (" + new_w + ", " + new_h + ")");
        activeDocument.resizeImage(new_w, new_h);
        file = new File('../etc/dots/dot'+(30-i)+'.png');
        opts = new PNGSaveOptions()
        opts.interlaced = false;
        activeDocument.saveAs(file, opts, true, Extension.LOWERCASE);
        activeDocument.activeHistoryState = activeDocument.historyStates[0];
    }
}

